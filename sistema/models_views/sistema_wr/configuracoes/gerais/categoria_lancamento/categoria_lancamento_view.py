from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sistema._utilitarios import *


@app.route("/configuracoes/gerais/categoria-lancamento/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_categoria_lancamento():
    try:
        inicializar_categorias_padrao()

        categorias_principais = CategoriaLancamentoModel.buscar_principais()

        estrutura = []
        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo(categoria.id)
            estrutura.append(categoria_dict)

        return render_template(
            "sistema_wr/configuracao/gerais/categoria_lancamento/categoria_lancamento.html", estrutura=estrutura
        )

    except Exception as e:
        flash((f"Erro ao carregar plano de contas: {str(e)}", "error"))
        return render_template(
            "sistema_wr/configuracao/gerais/categoria_lancamento/categoria_lancamento.html", estrutura=[]
        )


@app.route("/configuracoes/categoria-lancamento/criar", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria():
    try:
        data = request.get_json()
        parent_code = data.get("parent_code")
        nome = data.get("nome", "").strip()

        if not nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        if not parent_code:
            return jsonify({"erro": "Código pai é obrigatório"}), 400

        categoria_pai = CategoriaLancamentoModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            return jsonify({"erro": "Categoria pai não encontrada ou inativa"}), 404

        novo_codigo = CategoriaLancamentoModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            return jsonify({"erro": "Não foi possível gerar código"}), 400

        nivel = novo_codigo.count(".") + 1

        if not CategoriaLancamentoModel.verificar_codigo_disponivel(novo_codigo):
            for tentativa in range(1, 100):
                codigo_alternativo = CategoriaLancamentoModel.gerar_proximo_codigo(parent_code)
                if CategoriaLancamentoModel.verificar_codigo_disponivel(codigo_alternativo):
                    novo_codigo = codigo_alternativo
                    break
            else:
                return jsonify({"erro": "Não foi possível gerar código único"}), 400

        categoria_inativa = CategoriaLancamentoModel.query.filter_by(
            codigo=novo_codigo, 
            ativo=False
        ).first()
        
        if categoria_inativa:
            categoria_inativa.nome = nome
            categoria_inativa.tipo = categoria_pai.tipo
            categoria_inativa.parent_id = categoria_pai.id
            categoria_inativa.nivel = nivel
            categoria_inativa.ativo = True
            
            nova_categoria = categoria_inativa
            action_message = "reativada"
        else:
            nova_categoria = CategoriaLancamentoModel(
                codigo=novo_codigo,
                nome=nome,
                tipo=categoria_pai.tipo,
                parent_id=categoria_pai.id,
                nivel=nivel,
            )
            db.session.add(nova_categoria)
            action_message = "criada"

        db.session.commit()

        return jsonify(
            {
                "sucesso": True,
                "categoria": nova_categoria.to_dict(),
                "mensagem": f'Subcategoria "{nome}" {action_message} com sucesso! (Código: {novo_codigo})',
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500


@app.route("/configuracoes/categoria-lancamento/inativos", methods=["GET"])
@login_required
@requires_roles
def listar_categorias_inativas():
    try:
        categorias_inativas = CategoriaLancamentoModel.query.filter_by(ativo=False).order_by(CategoriaLancamentoModel.codigo).all()
        
        lista_inativas = []
        for cat in categorias_inativas:
            lista_inativas.append({
                'id': cat.id,
                'codigo': cat.codigo,
                'nome': cat.nome,
                'tipo': cat.tipo,
                'nivel': cat.nivel,
                'parent_id': cat.parent_id
            })
        
        return jsonify({
            'categorias_inativas': lista_inativas,
            'total': len(lista_inativas)
        })
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao listar inativos: {str(e)}"}), 500


@app.route("/configuracoes/categoria-lancamento/reativar/<int:categoria_id>", methods=["POST"])
@login_required
@requires_roles
def reativar_categoria(categoria_id):
    try:
        categoria = CategoriaLancamentoModel.query.get_or_404(categoria_id)
        
        if categoria.ativo:
            return jsonify({"erro": "Categoria já está ativa"}), 400
        
        conflito = CategoriaLancamentoModel.query.filter_by(
            codigo=categoria.codigo,
            ativo=True
        ).first()
        
        if conflito:
            return jsonify({
                "erro": f"Não é possível reativar: código {categoria.codigo} já está em uso"
            }), 400
        
        categoria.ativo = True
        db.session.commit()
        
        return jsonify({
            "sucesso": True,
            "categoria": categoria.to_dict(),
            "mensagem": f"Categoria '{categoria.nome}' reativada com sucesso!"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao reativar: {str(e)}"}), 500


@app.route(
    "/configuracoes/categoria-lancamento/editar/<int:categoria_id>", methods=["PUT"]
)
@login_required
@requires_roles
def editar_categoria(categoria_id):
    try:
        categoria = CategoriaLancamentoModel.query.get_or_404(categoria_id)
        data = request.get_json()
        novo_nome = data.get("nome", "").strip()

        if not novo_nome:
            return jsonify({"erro": "Nome é obrigatório"}), 400

        nome_anterior = categoria.nome
        categoria.nome = novo_nome
        db.session.commit()

        return jsonify(
            {
                "sucesso": True,
                "categoria": categoria.to_dict(),
                "mensagem": "Categoria atualizada com sucesso!",
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao atualizar: {str(e)}"}), 500


@app.route(
    "/configuracoes/categoria-lancamento/excluir/<int:categoria_id>", methods=["DELETE"]
)
@login_required
@requires_roles
def excluir_categoria(categoria_id):
    try:
        categoria = CategoriaLancamentoModel.query.get_or_404(categoria_id)

        filhos = categoria.get_children_ordenados()
        if filhos:
            return (
                jsonify(
                    {
                        "erro": "Não é possível excluir categoria que possui subcategorias ativas"
                    }
                ),
                400,
            )

        nome_categoria = categoria.nome
        categoria.ativo = False
        db.session.commit()

        return jsonify(
            {
                "sucesso": True,
                "mensagem": f'Categoria "{nome_categoria}" excluída com sucesso!',
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": f"Erro ao excluir: {str(e)}"}), 500


@app.route("/configuracoes/categoria-lancamento/api/estrutura", methods=["GET"])
@login_required
@requires_roles
def api_estrutura_categoria_lancamento():
    try:
        categorias_principais = CategoriaLancamentoModel.buscar_principais()
        estrutura = []

        for categoria in categorias_principais:
            categoria_dict = categoria.to_dict()
            categoria_dict["children"] = obter_subcategorias_recursivo(categoria.id)
            estrutura.append(categoria_dict)

        return jsonify({"estrutura": estrutura})

    except Exception as e:
        return jsonify({"erro": f"Erro ao carregar estrutura: {str(e)}"}), 500


def inicializar_categorias_padrao():
    categorias_padrao = [
        ("1", "Receitas", 1),
        ("2", "Despesas", 2),
        ("3", "Movimentação", 3),
    ]

    for codigo, nome, tipo in categorias_padrao:
        existe_ativa = CategoriaLancamentoModel.buscar_por_codigo(codigo)
        if not existe_ativa:
            categoria_inativa = CategoriaLancamentoModel.query.filter_by(
                codigo=codigo,
                ativo=False
            ).first()
            
            if categoria_inativa:
                categoria_inativa.nome = nome
                categoria_inativa.tipo = tipo
                categoria_inativa.ativo = True
            else:
                categoria = CategoriaLancamentoModel(
                    codigo=codigo, 
                    nome=nome, 
                    tipo=tipo, 
                    nivel=1
                )
                db.session.add(categoria)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar categorias padrão: {str(e)}")


def obter_subcategorias_recursivo(parent_id):
    subcategorias = CategoriaLancamentoModel.buscar_filhos(parent_id)
    resultado = []

    for sub in subcategorias:
        sub_dict = sub.to_dict()
        sub_dict["children"] = obter_subcategorias_recursivo(sub.id)
        resultado.append(sub_dict)

    return resultado


def limpar_codigos_orfaos():
    try:
        orfaos = CategoriaLancamentoModel.query.filter(
            CategoriaLancamentoModel.ativo == False,
            CategoriaLancamentoModel.parent_id.isnot(None)
        ).all()
        
        removidos = []
        for orfao in orfaos:
            pai = CategoriaLancamentoModel.query.filter_by(
                id=orfao.parent_id,
                ativo=True
            ).first()
            
            if not pai:
                removidos.append(f"{orfao.codigo} - {orfao.nome}")
                db.session.delete(orfao)
        
        db.session.commit()
        return removidos
        
    except Exception as e:
        db.session.rollback()
        raise


@app.route("/configuracoes/categoria-lancamento/criar-com-flash", methods=["POST"])
@login_required
@requires_roles
def criar_subcategoria_com_flash():
    try:
        parent_code = request.form.get("parent_code")
        nome = request.form.get("nome", "").strip()

        if not nome:
            flash(("Nome é obrigatório", "error"))
            return redirect(url_for("listar_categoria_lancamento"))

        if not parent_code:
            flash(("Código pai é obrigatório", "error"))
            return redirect(url_for("listar_categoria_lancamento"))

        categoria_pai = CategoriaLancamentoModel.buscar_por_codigo(parent_code)
        if not categoria_pai:
            flash(("Categoria pai não encontrada", "error"))
            return redirect(url_for("listar_categoria_lancamento"))

        novo_codigo = CategoriaLancamentoModel.gerar_proximo_codigo(parent_code)
        if not novo_codigo:
            flash(("Não foi possível gerar código", "error"))
            return redirect(url_for("listar_categoria_lancamento"))

        nivel = novo_codigo.count(".") + 1

        nova_categoria = CategoriaLancamentoModel(
            codigo=novo_codigo,
            nome=nome,
            tipo=categoria_pai.tipo,
            parent_id=categoria_pai.id,
            nivel=nivel,
        )

        db.session.add(nova_categoria)
        db.session.commit()

        flash((f'Subcategoria "{nome}" criada com sucesso!', "success"))

        return redirect(url_for("listar_categoria_lancamento"))

    except Exception as e:
        db.session.rollback()
        flash((f"Erro interno: {str(e)}", "error"))
        return redirect(url_for("listar_categoria_lancamento"))
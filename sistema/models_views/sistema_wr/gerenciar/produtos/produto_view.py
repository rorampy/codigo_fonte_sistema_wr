from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.produtos.produto_model import ProdutoModel
from sistema._utilitarios import *


# Obtem informações do produto para consumo no front end
@app.route("/gerenciar/produto/obter-produto/<int:id>", methods=["GET"])
@login_required
@requires_roles
def obter_produto(id):
    produto = ProdutoModel.obter_produto_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({
        "id": produto.id,
        "descricao": produto.descricao,
        "valor": produto.valor,
        "periodo": produto.periodo,
        "ativo": produto.ativo
    })


@app.route("/gerenciar/produto/listar", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_produtos():
    produtos = ProdutoModel.listar_produtos()
    return render_template("sistema_wr/gerenciar/produtos/produtos_listar.html", dados_corretos=request.form, produtos=produtos)


@app.route("/gerenciar/produto/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_produto():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    if request.method == "POST":
        descricao = request.form["descricao"]
        valor = request.form["valor"]
        periodo = request.form["periodo"]
        
        ativo_checkbox = request.form.get("ativo", "0")
        ativo = True if ativo_checkbox == "1" else False
        
        campos = {
            "descricao": ["Descrição do Produto", descricao],
            "valor": ["Valor", valor],
            "periodo": ["Período de Cobrança", periodo]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        
        if descricao:
            pesquisa_descricao_banco = ProdutoModel.query.filter_by(
                descricao=descricao
            ).first()
            if pesquisa_descricao_banco:
                gravar_banco = False
                validacao_campos_erros["descricao"] = "Já existe um produto com esta descrição!"
        
        if gravar_banco == True:
            try:
                produto = ProdutoModel(
                    descricao=descricao,
                    valor=(ValoresMonetarios.converter_string_brl_para_float(valor)*100),
                    periodo=periodo,
                    ativo=ativo
                )
                
                db.session.add(produto)
                db.session.commit()
                
                flash(("Produto cadastrado com sucesso!", "success"))
                return redirect(url_for("listar_produtos"))
                
            except Exception as e:
                db.session.rollback()
                gravar_banco = False
                flash(("Erro ao cadastrar produto. Tente novamente!", "danger"))
    
    return render_template(
        "sistema_wr/gerenciar/produtos/produto_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/produto/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_produto(id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    obter_produto = ProdutoModel.obter_produto_id(id)
    
    if not obter_produto:
        flash(("Produto não encontrado!", "error"))
        return redirect(url_for("listar_produtos"))
    
    if request.method == "POST":
        descricao = request.form["descricao"]
        valor = request.form["valor"]
        periodo = request.form["periodo"]
        
        ativo_checkbox = request.form.get("ativo", "0")
        ativo = True if ativo_checkbox == "1" else False
        
        campos = {
            "descricao": ["Descrição do Produto", descricao],
            "valor": ["Valor", valor],
            "periodo": ["Período de Cobrança", periodo]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        if descricao:
            pesquisa_descricao_banco = ProdutoModel.query.filter(
                ProdutoModel.descricao == descricao,
                ProdutoModel.id != id
            ).first()
            if pesquisa_descricao_banco:
                gravar_banco = False
                validacao_campos_erros["descricao"] = "Já existe um produto com esta descrição!"
        
        if gravar_banco == True:
            try:
                obter_produto.descricao = descricao
                obter_produto.valor = (ValoresMonetarios.converter_string_brl_para_float(valor)*100)
                obter_produto.periodo = periodo
                obter_produto.ativo = ativo

                db.session.commit()
                
                flash(("Produto atualizado com sucesso!", "success"))
                return redirect(url_for("listar_produtos"))
                
            except Exception as e:
                db.session.rollback()
                gravar_banco = False
                flash(("Erro ao atualizar produto. Tente novamente!", "danger"))
    
    return render_template(
        "sistema_wr/gerenciar/produtos/produto_editar.html",
        produto=obter_produto,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/produto/ativar/<int:id>", methods=["GET"])
@login_required
@requires_roles
def ativar_produto(id):
    obter_produto = ProdutoModel.obter_produto_id(id)
    
    if not obter_produto:
        flash(("Produto não encontrado!", "danger"))
        return redirect(url_for("listar_produtos"))
    
    try:
        obter_produto.ativo = True
        db.session.commit()
        
        flash(("Produto ativado com sucesso!", "success"))
        
    except Exception as e:
        db.session.rollback()
        flash(("Erro ao ativar produto. Tente novamente!", "danger"))
    
    return redirect(url_for("listar_produtos"))


@app.route("/gerenciar/produto/desativar/<int:id>", methods=["GET"])
@login_required
@requires_roles
def desativar_produto(id):
    obter_produto = ProdutoModel.obter_produto_id(id)
    
    if not obter_produto:
        flash(("Produto não encontrado!", "danger"))
        return redirect(url_for("listar_produtos"))
    
    try:
        obter_produto.ativo = False
        db.session.commit()
        
        flash(("Produto desativado com sucesso!", "success"))
        
    except Exception as e:
        db.session.rollback()
        flash(("Erro ao desativar produto. Tente novamente!", "danger"))
    
    return redirect(url_for("listar_produtos"))
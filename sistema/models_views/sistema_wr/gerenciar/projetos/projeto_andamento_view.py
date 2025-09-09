from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_andamento_model import AndamentoProjetoModel
from sistema._utilitarios import *


@app.route("/gerenciar/projetos/andamentos", methods=["GET", "POST"])
@login_required
@requires_roles
def andamentos_listar():
    if request.method == 'POST':
        nome_andamento = request.form.get('nomeAndamento')
        
        andamentos = AndamentoProjetoModel.query.filter(
            AndamentoProjetoModel.deletado == False
        )
        
        if nome_andamento:
            andamentos = andamentos.filter(
                AndamentoProjetoModel.nome.ilike(f"%{nome_andamento}%")
            )
        
        andamentos = andamentos.order_by(AndamentoProjetoModel.id.asc()).all()
        dados_corretos = request.form
    else:
        andamentos = AndamentoProjetoModel.query.filter(
            AndamentoProjetoModel.deletado == False
        ).order_by(AndamentoProjetoModel.id.asc()).all()
        dados_corretos = {}
    
    return render_template(
        "sistema_wr/configuracao/andamento_projeto/andamentos_listar.html",
        andamentos=andamentos,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/projetos/andamentos/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_cadastrar():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        nome_andamento = request.form["nomeAndamento"]

        campos = {
            "nomeAndamento": ["Nome do Andamento", nome_andamento],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        # Verificar se o andamento já existe
        andamento_existente = AndamentoProjetoModel.query.filter_by(
            nome=nome_andamento,
            deletado=False
        ).first()
        
        if andamento_existente:
            gravar_banco = False
            validacao_campos_erros["nomeAndamento"] = "Já existe um andamento com este nome"

        if gravar_banco:
            andamento = AndamentoProjetoModel(
                nome=nome_andamento
            )
            
            db.session.add(andamento)
            db.session.commit()
            flash((f"Andamento cadastrado com sucesso!", "success"))
            return redirect(url_for("andamentos_listar"))

    return render_template(
        "sistema_wr/configuracao/andamento_projeto/andamento_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/projetos/andamento/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_editar(id):
    andamento = AndamentoProjetoModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento não encontrado!", "warning"))
        return redirect(url_for("andamentos_listar"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    dados_corretos = {
        "nomeAndamento": andamento.nome,
    }

    if request.method == "POST":
        nome_andamento = request.form["nomeAndamento"]

        campos = {
            "nomeAndamento": ["Nome do Andamento", nome_andamento],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        # Verificar se o nome do andamento já existe (exceto o atual)
        andamento_existente = AndamentoProjetoModel.query.filter(
            AndamentoProjetoModel.nome == nome_andamento,
            AndamentoProjetoModel.deletado == False,
            AndamentoProjetoModel.id != id
        ).first()
        
        if andamento_existente:
            gravar_banco = False
            validacao_campos_erros["nomeAndamento"] = "Já existe um andamento com este nome"

        if gravar_banco:
            andamento.nome = nome_andamento
            db.session.commit()
            flash((f"Andamento editado com sucesso!", "success"))
            return redirect(url_for("andamentos_listar"))

    return render_template(
        "sistema_wr/configuracao/andamento_projeto/andamento_editar.html",
        andamento=andamento,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/desativar/andamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_desativar(id):
    andamento = AndamentoProjetoModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento não encontrado!", "warning"))
        return redirect(url_for("andamentos_listar"))

    # Verificar se há projetos usando este andamento
    from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
    projetos_usando = ProjetoModel.query.filter(
        ProjetoModel.andamento_id == id,
        ProjetoModel.deletado == False
    ).count()
    
    if projetos_usando > 0:
        flash((f"Não é possível desativar este andamento. Existem {projetos_usando} projeto(s) utilizando-o.", "warning"))
        return redirect(url_for("andamentos_listar"))

    andamento.ativo = False
    db.session.commit()
    flash((f"Andamento desativado com sucesso!", "success"))
    return redirect(url_for("andamentos_listar"))


@app.route("/gerenciar/ativar/andamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_ativar(id):
    andamento = AndamentoProjetoModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento não encontrado!", "warning"))
        return redirect(url_for("andamentos_listar"))

    andamento.ativo = True
    db.session.commit()
    flash((f"Andamento ativado com sucesso!", "success"))
    return redirect(url_for("andamentos_listar"))


@app.route("/gerenciar/excluir/andamento/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_excluir(id):
    andamento = AndamentoProjetoModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento não encontrado!", "warning"))
        return redirect(url_for("andamentos_listar"))

    # Verificar se há projetos usando este andamento
    from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
    projetos_usando = ProjetoModel.query.filter(
        ProjetoModel.andamento_id == id,
        ProjetoModel.deletado == False
    ).count()
    
    if projetos_usando > 0:
        flash((f"Não é possível excluir este andamento. Existem {projetos_usando} projeto(s) utilizando-o.", "warning"))
        return redirect(url_for("andamentos_listar"))

    andamento.deletado = True
    andamento.ativo = False
    db.session.commit()
    flash((f"Andamento excluído com sucesso!", "success"))
    return redirect(url_for("andamentos_listar"))

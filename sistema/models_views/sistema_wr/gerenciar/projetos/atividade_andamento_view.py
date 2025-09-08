from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_andamento_model import AndamentoAtividadeModel
from sistema._utilitarios import *


@app.route("/gerenciar/atividades/andamentos", methods=["GET", "POST"])
@login_required
@requires_roles
def andamentos_atividade_listar():
    if request.method == 'POST':
        nome_andamento = request.form.get('nomeAndamento')
        
        andamentos = AndamentoAtividadeModel.obter_andamentos_asc_nome()
        
        if nome_andamento:
            andamentos = andamentos.filter(
                AndamentoAtividadeModel.nome.ilike(f"%{nome_andamento}%")
            )
        dados_corretos = request.form
    else:
        andamentos = AndamentoAtividadeModel.obter_andamentos_asc_nome()
        dados_corretos = {}
    
    return render_template(
        "sistema_hash/configuracao/andamento_atividade/andamentos_atividade_listar.html",
        andamentos=andamentos,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/atividades/andamentos/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_atividade_cadastrar():
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
        andamento_existente = AndamentoAtividadeModel.query.filter_by(
            nome=nome_andamento,
            deletado=False
        ).first()
        
        if andamento_existente:
            gravar_banco = False
            validacao_campos_erros["nomeAndamento"] = "Já existe um andamento de atividade com este nome"

        if gravar_banco:
            andamento = AndamentoAtividadeModel(
                nome=nome_andamento
            )
            
            db.session.add(andamento)
            db.session.commit()
            flash((f"Andamento de atividade cadastrado com sucesso!", "success"))
            return redirect(url_for("andamentos_atividade_listar"))

    return render_template(
        "sistema_hash/configuracao/andamento_atividade/andamento_atividade_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/atividades/andamento/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_atividade_editar(id):
    andamento = AndamentoAtividadeModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento de atividade não encontrado!", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

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
        andamento_existente = AndamentoAtividadeModel.query.filter(
            AndamentoAtividadeModel.nome == nome_andamento,
            AndamentoAtividadeModel.deletado == False,
            AndamentoAtividadeModel.id != id
        ).first()
        
        if andamento_existente:
            gravar_banco = False
            validacao_campos_erros["nomeAndamento"] = "Já existe um andamento de atividade com este nome"

        if gravar_banco:
            andamento.nome = nome_andamento
            db.session.commit()
            flash((f"Andamento de atividade editado com sucesso!", "success"))
            return redirect(url_for("andamentos_atividade_listar"))

    return render_template(
        "sistema_hash/configuracao/andamento_atividade/andamento_atividade_editar.html",
        andamento=andamento,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/desativar/andamento_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_atividade_desativar(id):
    andamento = AndamentoAtividadeModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento de atividade não encontrado!", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

    # Verificar se há atividades usando este andamento
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    atividades_usando = AtividadeModel.query.filter(
        AtividadeModel.situacao_id == id,
        AtividadeModel.deletado == False
    ).count()
    
    if atividades_usando > 0:
        flash((f"Não é possível desativar este andamento. Existem {atividades_usando} atividade(s) utilizando-o.", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

    andamento.ativo = False
    db.session.commit()
    flash((f"Andamento de atividade desativado com sucesso!", "success"))
    return redirect(url_for("andamentos_atividade_listar"))


@app.route("/gerenciar/ativar/andamento_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_atividade_ativar(id):
    andamento = AndamentoAtividadeModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento de atividade não encontrado!", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

    andamento.ativo = True
    db.session.commit()
    flash((f"Andamento de atividade ativado com sucesso!", "success"))
    return redirect(url_for("andamentos_atividade_listar"))


@app.route("/gerenciar/excluir/andamento_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def andamento_atividade_excluir(id):
    andamento = AndamentoAtividadeModel.obter_andamento_por_id(id)
    if andamento is None:
        flash((f"Andamento de atividade não encontrado!", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

    # Verifica se há atividades usando este andamento
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    atividades_usando = AtividadeModel.query.filter(
        AtividadeModel.situacao_id == id,
        AtividadeModel.deletado == False
    ).count()
    
    if atividades_usando > 0:
        flash((f"Não é possível excluir este andamento. Existem {atividades_usando} atividade(s) utilizando-o.", "warning"))
        return redirect(url_for("andamentos_atividade_listar"))

    andamento.deletado = True
    andamento.ativo = False
    db.session.commit()
    flash((f"Andamento de atividade excluído com sucesso!", "success"))
    return redirect(url_for("andamentos_atividade_listar"))

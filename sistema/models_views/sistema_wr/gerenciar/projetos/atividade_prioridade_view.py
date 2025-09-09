from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_prioridade_model import PrioridadeAtividadeModel
from sistema._utilitarios import *


@app.route("/gerenciar/atividades/prioridades", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridades_atividade_listar():
    if request.method == 'POST':
        nome_prioridade = request.form.get('nomePrioridade')
        
        prioridades = PrioridadeAtividadeModel.obter_prioridades_asc_nome()
        
        if nome_prioridade:
            prioridades = prioridades.filter(
                PrioridadeAtividadeModel.nome.ilike(f"%{nome_prioridade}%")
            )
            
        dados_corretos = request.form
    else:
        prioridades = PrioridadeAtividadeModel.obter_prioridades_asc_nome()
        dados_corretos = {}
    
    return render_template(
        "sistema_wr/configuracao/prioridade_atividade/prioridades_atividade_listar.html",
        prioridades=prioridades,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/atividades/prioridades/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridade_atividade_cadastrar():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        nome_prioridade = request.form["nomePrioridade"]
        ordem_prioridade = request.form["ordemPrioridade"]

        campos = {
            "nomePrioridade": ["Nome da Prioridade", nome_prioridade],
            "ordemPrioridade": ["Ordem de Exibição", ordem_prioridade],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        # Verificar se a prioridade já existe
        prioridade_existente = PrioridadeAtividadeModel.query.filter_by(
            nome=nome_prioridade,
            deletado=False
        ).first()
        
        if prioridade_existente:
            gravar_banco = False
            validacao_campos_erros["nomePrioridade"] = "Já existe uma prioridade com este nome"

        # Verificar se a ordem já está em uso
        ordem_existente = PrioridadeAtividadeModel.query.filter_by(
            ordem=int(ordem_prioridade),
            deletado=False
        ).first()
        
        if ordem_existente:
            gravar_banco = False
            validacao_campos_erros["ordemPrioridade"] = "Já existe uma prioridade com esta ordem"

        # Validar se ordem é um número positivo
        try:
            ordem = int(ordem_prioridade)
            if ordem <= 0:
                gravar_banco = False
                validacao_campos_erros["ordemPrioridade"] = "A ordem deve ser um número positivo"
        except ValueError:
            gravar_banco = False
            validacao_campos_erros["ordemPrioridade"] = "A ordem deve ser um número válido"

        if gravar_banco:
            prioridade = PrioridadeAtividadeModel(
                nome=nome_prioridade,
                ordem=ordem
            )
            
            db.session.add(prioridade)
            db.session.commit()
            flash((f"Prioridade de atividade cadastrada com sucesso!", "success"))
            return redirect(url_for("prioridades_atividade_listar"))

    return render_template(
        "sistema_wr/configuracao/prioridade_atividade/prioridade_atividade_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/atividades/prioridade/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridade_atividade_editar(id):
    prioridade = PrioridadeAtividadeModel.obter_prioridade_por_id(id)
    if prioridade is None:
        flash((f"Prioridade de atividade não encontrada!", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    dados_corretos = {
        "nomePrioridade": prioridade.nome,
        "ordemPrioridade": str(prioridade.ordem),
    }

    if request.method == "POST":
        nome_prioridade = request.form["nomePrioridade"]
        ordem_prioridade = request.form["ordemPrioridade"]

        campos = {
            "nomePrioridade": ["Nome da Prioridade", nome_prioridade],
            "ordemPrioridade": ["Ordem de Exibição", ordem_prioridade],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        # Verificar se o nome da prioridade já existe (exceto a atual)
        prioridade_existente = PrioridadeAtividadeModel.query.filter(
            PrioridadeAtividadeModel.nome == nome_prioridade,
            PrioridadeAtividadeModel.deletado == False,
            PrioridadeAtividadeModel.id != id
        ).first()
        
        if prioridade_existente:
            gravar_banco = False
            validacao_campos_erros["nomePrioridade"] = "Já existe uma prioridade com este nome"

        # Verificar se a ordem já está em uso (exceto a atual)
        ordem_existente = PrioridadeAtividadeModel.query.filter(
            PrioridadeAtividadeModel.ordem == int(ordem_prioridade),
            PrioridadeAtividadeModel.deletado == False,
            PrioridadeAtividadeModel.id != id
        ).first()
        
        if ordem_existente:
            gravar_banco = False
            validacao_campos_erros["ordemPrioridade"] = "Já existe uma prioridade com esta ordem"

        # Validar se ordem é um número positivo
        try:
            ordem = int(ordem_prioridade)
            if ordem <= 0:
                gravar_banco = False
                validacao_campos_erros["ordemPrioridade"] = "A ordem deve ser um número positivo"
        except ValueError:
            gravar_banco = False
            validacao_campos_erros["ordemPrioridade"] = "A ordem deve ser um número válido"

        if gravar_banco:
            prioridade.nome = nome_prioridade
            prioridade.ordem = ordem
            db.session.commit()
            flash((f"Prioridade de atividade editada com sucesso!", "success"))
            return redirect(url_for("prioridades_atividade_listar"))

    return render_template(
        "sistema_wr/configuracao/prioridade_atividade/prioridade_atividade_editar.html",
        prioridade=prioridade,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos,
    )


@app.route("/gerenciar/desativar/prioridade_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridade_atividade_desativar(id):
    prioridade = PrioridadeAtividadeModel.obter_prioridade_por_id(id)
    if prioridade is None:
        flash((f"Prioridade de atividade não encontrada!", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    # Verificar se há atividades usando esta prioridade
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    atividades_usando = AtividadeModel.query.filter(
        AtividadeModel.prioridade_id == id,
        AtividadeModel.deletado == False
    ).count()
    
    if atividades_usando > 0:
        flash((f"Não é possível desativar esta prioridade. Existem {atividades_usando} atividade(s) utilizando-a.", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    prioridade.ativo = False
    db.session.commit()
    flash((f"Prioridade de atividade desativada com sucesso!", "success"))
    return redirect(url_for("prioridades_atividade_listar"))


@app.route("/gerenciar/ativar/prioridade_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridade_atividade_ativar(id):
    prioridade = PrioridadeAtividadeModel.obter_prioridade_por_id(id)
    if prioridade is None:
        flash((f"Prioridade de atividade não encontrada!", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    prioridade.ativo = True
    db.session.commit()
    flash((f"Prioridade de atividade ativada com sucesso!", "success"))
    return redirect(url_for("prioridades_atividade_listar"))


@app.route("/gerenciar/excluir/prioridade_atividade/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def prioridade_atividade_excluir(id):
    prioridade = PrioridadeAtividadeModel.obter_prioridade_por_id(id)
    if prioridade is None:
        flash((f"Prioridade de atividade não encontrada!", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    # Verificar se há atividades usando esta prioridade
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    atividades_usando = AtividadeModel.query.filter(
        AtividadeModel.prioridade_id == id,
        AtividadeModel.deletado == False
    ).count()
    
    if atividades_usando > 0:
        flash((f"Não é possível excluir esta prioridade. Existem {atividades_usando} atividade(s) utilizando-a.", "warning"))
        return redirect(url_for("prioridades_atividade_listar"))

    prioridade.deletado = True
    prioridade.ativo = False
    db.session.commit()
    flash((f"Prioridade de atividade excluída com sucesso!", "success"))
    return redirect(url_for("prioridades_atividade_listar"))

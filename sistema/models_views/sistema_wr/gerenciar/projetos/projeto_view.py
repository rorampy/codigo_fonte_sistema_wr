from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_andamento_model import AndamentoProjetoModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema._utilitarios import *
from datetime import datetime, date


@app.route("/gerenciar/projetos", methods=["GET", "POST"])
@login_required
@requires_roles
def projetos_listar():
    if request.method == 'POST':
        projetos = ProjetoModel.filtrar_projetos(
            nome_projeto=request.form.get('nomeProjeto'),
            responsavel_tecnico=request.form.get('responsavelTecnico'),
            andamento_id=request.form.get('andamentoProjeto')
        )
        dados_corretos = request.form
    else:
        projetos = ProjetoModel.listar_projetos()
        dados_corretos = {}
    
    andamentos = AndamentoProjetoModel.listar_andamentos_ativos()
    
    return render_template(
        "sistema_hash/gerenciar/projetos/projetos_listar.html",
        projetos=projetos,
        andamentos=andamentos,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/projetos/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def projeto_cadastrar():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    usuarios_ativos = UsuarioModel.obter_usuarios_desc_id()
    andamentos = AndamentoProjetoModel.listar_andamentos_ativos()

    if request.method == "POST":
        nome_projeto = request.form["nomeProjeto"]
        data_inicio = request.form["dataInicio"]
        data_fim = request.form["dataFim"]
        responsavel_tecnico_id = request.form["responsavelTecnico"]
        usuarios_envolvidos = request.form.getlist("usuariosEnvolvidos")
        observacoes = request.form["observacoes"]
        andamento_id = request.form["andamentoProjeto"]

        campos = {
            "nomeProjeto": ["Nome do Projeto", nome_projeto],
            "dataInicio": ["Data de Início", data_inicio],
            "responsavelTecnico": ["Responsável Técnico", responsavel_tecnico_id],
            "andamentoProjeto": ["Andamento", andamento_id]
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        # Validação de data
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                if data_fim:
                    data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                    if data_fim_obj <= data_inicio_obj:
                        gravar_banco = False
                        validacao_campos_erros["dataFim"] = "Data de fim deve ser posterior à data de início"
            except ValueError:
                gravar_banco = False
                validacao_campos_erros["dataInicio"] = "Data inválida"

        # Verificar se o projeto já existe
        projeto_existente = ProjetoModel.query.filter_by(
            nome_projeto=nome_projeto,
            deletado=False
        ).first()
        
        if projeto_existente:
            gravar_banco = False
            validacao_campos_erros["nomeProjeto"] = "Já existe um projeto com este nome"

        if gravar_banco:
            data_fim_obj = None
            if data_fim:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()

            projeto = ProjetoModel(
                nome_projeto=nome_projeto,
                data_inicio=datetime.strptime(data_inicio, '%Y-%m-%d').date(),
                data_fim=data_fim_obj,
                responsavel_tecnico_id=responsavel_tecnico_id,
                observacoes=observacoes,
                andamento_id=andamento_id
            )
            
            db.session.add(projeto)
            db.session.flush()

            # Adicionar usuários envolvidos
            for usuario_id in usuarios_envolvidos:
                if usuario_id:
                    projeto.adicionar_usuario_envolvido(usuario_id)

            db.session.commit()
            flash((f"Projeto cadastrado com sucesso!", "success"))
            return redirect(url_for("projetos_listar"))

    return render_template(
        "sistema_hash/gerenciar/projetos/projeto_cadastrar.html",
        usuarios_ativos=usuarios_ativos,
        andamentos=andamentos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )


@app.route("/gerenciar/projeto/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def projeto_editar(id):
    projeto = ProjetoModel.obter_projeto_por_id(id)
    if projeto is None:
        flash((f"Projeto não encontrado!", "warning"))
        return redirect(url_for("projetos_listar"))

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    usuarios_ativos = UsuarioModel.obter_usuarios_desc_id()
    andamentos = AndamentoProjetoModel.listar_andamentos_ativos()

    if request.method == "POST":
        nome_projeto = request.form["nomeProjeto"]
        data_inicio = request.form["dataInicio"]
        data_fim = request.form["dataFim"]
        responsavel_tecnico_id = request.form["responsavelTecnico"]
        usuarios_envolvidos = request.form.getlist("usuariosEnvolvidos")
        observacoes = request.form["observacoes"]
        andamento_id = request.form["andamentoProjeto"]

        campos = {
            "nomeProjeto": ["Nome do Projeto", nome_projeto],
            "dataInicio": ["Data de Início", data_inicio],
            "responsavelTecnico": ["Responsável Técnico", responsavel_tecnico_id],
            "andamentoProjeto": ["Andamento", andamento_id],
        }

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))

        data_fim_obj = None
        # Validação de data
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                if data_fim:
                    data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                    if data_fim_obj <= data_inicio_obj:
                        gravar_banco = False
                        validacao_campos_erros["dataFim"] = "Data de fim deve ser posterior à data de início"
            except ValueError:
                gravar_banco = False
                validacao_campos_erros["dataInicio"] = "Data inválida"

        # Verificar se o nome do projeto já existe (exceto o atual)
        projeto_existente = ProjetoModel.query.filter(
            ProjetoModel.nome_projeto == nome_projeto,
            ProjetoModel.deletado == False,
            ProjetoModel.id != id
        ).first()
        
        if projeto_existente:
            gravar_banco = False
            validacao_campos_erros["nomeProjeto"] = "Já existe um projeto com este nome"
            
        if andamento_id == "4":  # 4 = Concluído
            from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
            
            # Atividades do projeto que não estão concluídas nem canceladas
            atividades_pendentes = AtividadeModel.query.filter(
                AtividadeModel.projeto_id == id,
                AtividadeModel.deletado == False,
                AtividadeModel.situacao_id.notin_([4, 5])  # 4=Concluída, 5=Cancelada
            ).all()
            
            if atividades_pendentes:
                gravar_banco = False
                flash((f"O projeto não pode ser concluído pois possui atividades em aberto!", "warning"))
                return redirect(url_for("projeto_editar", id=id))

        if gravar_banco:
            # Atualizar projeto
            projeto.nome_projeto = nome_projeto
            projeto.data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            projeto.data_fim = data_fim_obj
            projeto.responsavel_tecnico_id = responsavel_tecnico_id
            projeto.observacoes = observacoes
            projeto.andamento_id = andamento_id

            # Atualizar usuários envolvidos
            projeto.usuarios_envolvidos.clear()
            for usuario_id in usuarios_envolvidos:
                if usuario_id:
                    projeto.adicionar_usuario_envolvido(usuario_id)

            db.session.commit()
            flash((f"Projeto editado com sucesso!", "success"))
            return redirect(url_for("projetos_listar"))

    return render_template(
        "sistema_hash/gerenciar/projetos/projeto_editar.html",
        projeto=projeto,
        usuarios_ativos=usuarios_ativos,
        andamentos=andamentos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form
    )


@app.route("/gerenciar/projeto/detalhes/<int:id>", methods=["GET"])
@login_required
@requires_roles
def projeto_detalhes(id):
    projeto = ProjetoModel.obter_projeto_por_id(id)
    
    data_hoje = date.today()
    
    if projeto is None:
        flash((f"Projeto não encontrado!", "warning"))
        return redirect(url_for("projetos_listar"))

    return render_template(
        "sistema_hash/gerenciar/projetos/projeto_detalhes.html",
        projeto=projeto,
        data_hoje = data_hoje
    )


@app.route("/gerenciar/desativar/projeto/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def projeto_desativar(id):
    projeto = ProjetoModel.obter_projeto_por_id(id)
    if projeto is None:
        flash((f"Projeto não encontrado!", "warning"))
        return redirect(url_for("projetos_listar"))
    
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    atividades = AtividadeModel.listar_atividades_por_projeto(id)
    if atividades:
        flash((f"O Projeto não pode ser desativado póis já possui atividades!", "warning"))
        return redirect(url_for("projetos_listar"))
    
    if projeto.andamento_id != 1:
        flash((f"O Projeto não pode ser desativado pois já foi iniciado!", "warning"))
        return redirect(url_for("projetos_listar"))

    projeto.ativo = False
    db.session.commit()
    flash((f"Projeto desativado com sucesso!", "success"))
    return redirect(url_for("projetos_listar"))


@app.route("/gerenciar/ativar/projeto/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def projeto_ativar(id):
    projeto = ProjetoModel.obter_projeto_por_id(id)
    if projeto is None:
        flash((f"Projeto não encontrado!", "warning"))
        return redirect(url_for("projetos_listar"))

    projeto.ativo = True
    db.session.commit()
    flash((f"Projeto ativado com sucesso!", "success"))
    return redirect(url_for("projetos_listar"))

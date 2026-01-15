from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.projetos.lancamento_horas_model import LancamentoHorasModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema._utilitarios import *
from datetime import datetime, date


@app.route("/gerenciar/lancamento-horas")
@app.route("/gerenciar/lancamento-horas/<int:atividade_id>")
@login_required
@requires_roles
def lancamento_horas_listar(atividade_id=None):
    filtro_atividade = request.args.get('atividade_id', atividade_id)
    filtro_usuario = request.args.get('usuario_id')
    filtro_data_inicio = request.args.get('data_inicio')
    filtro_data_fim = request.args.get('data_fim')
    filtro_projeto = request.args.get('projeto_id')
    
    if filtro_atividade and filtro_atividade.strip():
        try:
            filtro_atividade = int(filtro_atividade)
        except (ValueError, TypeError):
            filtro_atividade = None
    else:
        filtro_atividade = None
    
    if filtro_usuario and filtro_usuario.strip():
        try:
            filtro_usuario = int(filtro_usuario)
        except (ValueError, TypeError):
            filtro_usuario = None
    else:
        filtro_usuario = None
    
    if filtro_projeto and filtro_projeto.strip():
        try:
            filtro_projeto = int(filtro_projeto)
        except (ValueError, TypeError):
            filtro_projeto = None
    else:
        filtro_projeto = None
        
    data_inicio_obj = None
    data_fim_obj = None
    if filtro_data_inicio:
        try:
            data_inicio_obj = DataHora.converter_data_str_em_objeto_datetime(filtro_data_inicio).date()
        except ValueError:
            pass
    if filtro_data_fim:
        try:
            data_fim_obj = DataHora.converter_data_str_em_objeto_datetime(filtro_data_fim).date()
        except ValueError:
            pass
    
    lancamentos = LancamentoHorasModel.query.join(
        AtividadeModel, LancamentoHorasModel.atividade_id == AtividadeModel.id
    ).join(
        ProjetoModel, AtividadeModel.projeto_id == ProjetoModel.id
    ).filter(
        LancamentoHorasModel.deletado == False
    )
    
    if filtro_atividade:
        lancamentos = lancamentos.filter(LancamentoHorasModel.atividade_id == filtro_atividade)
    
    if filtro_usuario:
        lancamentos = lancamentos.filter(LancamentoHorasModel.usuario_id == filtro_usuario)
    
    if filtro_projeto:
        lancamentos = lancamentos.filter(AtividadeModel.projeto_id == filtro_projeto)
    
    if data_inicio_obj:
        lancamentos = lancamentos.filter(LancamentoHorasModel.data_lancamento >= data_inicio_obj)
    
    if data_fim_obj:
        lancamentos = lancamentos.filter(LancamentoHorasModel.data_lancamento <= data_fim_obj)
    
    lancamentos = lancamentos.order_by(
        LancamentoHorasModel.data_lancamento.desc(),
        LancamentoHorasModel.data_cadastro.desc()
    ).all()
    
    # Dados para os filtros
    projetos = ProjetoModel.obter_projetos_asc_nome()
    atividades = AtividadeModel.query.filter(AtividadeModel.deletado == False).order_by(AtividadeModel.titulo.asc()).all()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()
    
    # Atividade específica se filtrada
    atividade_filtrada = None
    if filtro_atividade:
        atividade_filtrada = AtividadeModel.obter_atividade_por_id(filtro_atividade)
    
    # Calcular métricas se filtrado por usuário e user é admin
    metricas_usuario = None
    if filtro_usuario:
        from sqlalchemy import func, extract
        
        hoje = date.today()
        
        # 1. Total de horas (conforme filtro aplicado - dos lançamentos já filtrados)
        total_horas = sum(l.horas_gastas for l in lancamentos)
        
        # 2. Atividades fechadas no período
        query_atividades = AtividadeModel.query.filter(
            AtividadeModel.desenvolvedor_id == filtro_usuario,
            AtividadeModel.situacao_id == 4,  # Concluída
            AtividadeModel.deletado == False
        )
        if data_inicio_obj:
            query_atividades = query_atividades.filter(
                AtividadeModel.data_prazo_conclusao >= data_inicio_obj
            )
        if data_fim_obj:
            query_atividades = query_atividades.filter(
                AtividadeModel.data_prazo_conclusao <= data_fim_obj
            )
        atividades_fechadas = query_atividades.count()
        
        # 3. Horas hoje
        horas_hoje = db.session.query(func.sum(LancamentoHorasModel.horas_gastas)).filter(
            LancamentoHorasModel.usuario_id == filtro_usuario,
            LancamentoHorasModel.deletado == False,
            LancamentoHorasModel.data_lancamento == hoje
        ).scalar() or 0.0
        
        # 4. Horas no mês atual
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        
        horas_mes_atual = db.session.query(func.sum(LancamentoHorasModel.horas_gastas)).filter(
            LancamentoHorasModel.usuario_id == filtro_usuario,
            LancamentoHorasModel.deletado == False,
            LancamentoHorasModel.data_lancamento >= primeiro_dia_mes,
            LancamentoHorasModel.data_lancamento <= hoje
        ).scalar() or 0.0
        
        metricas_usuario = {
            'total_horas': round(total_horas, 1),
            'atividades_fechadas': atividades_fechadas,
            'horas_hoje': round(horas_hoje, 1),
            'horas_mes_atual': round(horas_mes_atual, 1),
            'data_hoje': DataHora.converter_data_de_en_para_br(hoje)
        }
    
    return render_template(
        "sistema_wr/gerenciar/projetos/lancamento_horas_listar.html",
        lancamentos=lancamentos,
        projetos=projetos,
        atividades=atividades,
        usuarios=usuarios,
        atividade_filtrada=atividade_filtrada,
        metricas_usuario=metricas_usuario,
        filtros={
            'atividade_id': filtro_atividade,
            'usuario_id': filtro_usuario,
            'projeto_id': filtro_projeto,
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim')
        }
    )


@app.route("/gerenciar/lancamento-horas/cadastrar", methods=["GET", "POST"])
@app.route("/gerenciar/lancamento-horas/cadastrar/<int:atividade_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancamento_horas_cadastrar(atividade_id=None):
    """Cadastra novo lançamento de horas"""
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    projetos = ProjetoModel.obter_projetos_asc_nome()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()
    
    # Se atividade_id fornecida busca atividades desse projeto
    atividades = []
    atividade_selecionada = None
    if atividade_id:
        atividade_selecionada = AtividadeModel.obter_atividade_por_id(atividade_id)
        if atividade_selecionada:
            atividades = AtividadeModel.listar_atividades_por_projeto(atividade_selecionada.projeto_id)
    else:
        atividades = AtividadeModel.query.filter(AtividadeModel.deletado == False).order_by(AtividadeModel.titulo.asc()).all()
    
    if request.method == "POST":
        atividade_id_form = request.form.get("atividadeId")
        usuario_id = request.form.get("usuarioId")
        data_lancamento = request.form.get("dataLancamento")
        descricao = request.form.get("descricao")
        horas_gastas = request.form.get("horasGastas")
        
        campos = {
            "atividadeId": ["Atividade", atividade_id_form],
            "usuarioId": ["Usuário", usuario_id],
            "dataLancamento": ["Data do Lançamento", data_lancamento],
            "descricao": ["Descrição", descricao],
            "horasGastas": ["Horas Gastas", horas_gastas]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        horas_processadas = 0.0
        if horas_gastas:
            try:
                horas_processadas = float(horas_gastas.replace(',', '.'))
                if horas_processadas <= 0:
                    validacao_campos_erros["horasGastas"] = "Horas gastas deve ser maior que zero"
                    gravar_banco = False
                elif horas_processadas > 24:
                    validacao_campos_erros["horasGastas"] = "Horas gastas não pode exceder 24 horas por dia"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["horasGastas"] = "Valor inválido para horas gastas"
                gravar_banco = False
        
        data_lancamento_obj = None
        if data_lancamento:
            try:
                data_lancamento_obj = DataHora.converter_data_str_em_objeto_datetime(data_lancamento).date()
                if data_lancamento_obj > date.today():
                    validacao_campos_erros["dataLancamento"] = "Data não pode ser futura"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["dataLancamento"] = "Data inválida"
                gravar_banco = False
        
        if atividade_id_form:
            atividade = AtividadeModel.obter_atividade_por_id(atividade_id_form)
            if not atividade:
                validacao_campos_erros["atividadeId"] = "Atividade não encontrada"
                gravar_banco = False
        
        if gravar_banco:
            try:

                # Verifica se horas necessárias foram definidas
                if atividade.horas_necessarias <= 0:
                    flash(("As horas estimadas não foram definidas!", "warning"))
                    return redirect(url_for("lancamento_horas_cadastrar", atividade_id=atividade_id_form))

                lancamento = LancamentoHorasModel(
                    atividade_id=atividade_id_form,
                    usuario_id=usuario_id,
                    data_lancamento=data_lancamento_obj,
                    descricao=descricao,
                    horas_gastas=horas_processadas
                )
                
                # método save customizado que atualiza automaticamente as horas da atividade
                lancamento.save()
                
                flash(("Lançamento de horas cadastrado com sucesso!", "success"))
                
                # Redireciona baseado na origem
                if atividade_id:
                    return redirect(url_for("atividade_visualizar", atividade_id=atividade_id))
                else:
                    return redirect(url_for("lancamento_horas_listar"))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao cadastrar lançamento: {str(e)}", "error"))
                gravar_banco = False
    
    return render_template(
        "sistema_wr/gerenciar/projetos/lancamento_horas_cadastrar.html",
        projetos=projetos,
        atividades=atividades,
        usuarios=usuarios,
        atividade_selecionada=atividade_selecionada,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
        atividade_id_url=atividade_id
    )


@app.route("/gerenciar/lancamento-horas/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancamento_horas_editar(id): 
    lancamento = LancamentoHorasModel.obter_lancamento_por_id(id)
    if not lancamento:
        flash(("Lançamento não encontrado!", "warning"))
        return redirect(url_for("lancamento_horas_listar"))
    
    # Verifica se a atividade foi concluída (fechada)
    if lancamento.atividade.situacao_id == 4:  # 4 = Concluída
        flash(("Não é possível editar lançamento de horas de uma atividade concluída!", "warning"))
        return redirect(url_for("lancamento_horas_listar"))
    
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    projetos = ProjetoModel.obter_projetos_asc_nome()
    atividades = AtividadeModel.query.filter(AtividadeModel.deletado == False).order_by(AtividadeModel.titulo.asc()).all()
    usuarios = UsuarioModel.obter_usuarios_asc_nome()
    
    if request.method == "POST":
        atividade_id = request.form.get("atividadeId")
        usuario_id = request.form.get("usuarioId")
        data_lancamento = request.form.get("dataLancamento")
        descricao = request.form.get("descricao")
        horas_gastas = request.form.get("horasGastas")
        
        campos = {
            "atividadeId": ["Atividade", atividade_id],
            "usuarioId": ["Usuário", usuario_id],
            "dataLancamento": ["Data do Lançamento", data_lancamento],
            "descricao": ["Descrição", descricao],
            "horasGastas": ["Horas Gastas", horas_gastas]
        }
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if "validado" not in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))
        
        horas_processadas = 0.0
        if horas_gastas:
            try:
                horas_processadas = float(horas_gastas.replace(',', '.'))
                if horas_processadas <= 0:
                    validacao_campos_erros["horasGastas"] = "Horas gastas deve ser maior que zero"
                    gravar_banco = False
                elif horas_processadas > 24:
                    validacao_campos_erros["horasGastas"] = "Horas gastas não pode exceder 24 horas por dia"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["horasGastas"] = "Valor inválido para horas gastas"
                gravar_banco = False
        
        data_lancamento_obj = None
        if data_lancamento:
            try:
                data_lancamento_obj = DataHora.converter_data_str_em_objeto_datetime(data_lancamento).date()
                if data_lancamento_obj > date.today():
                    validacao_campos_erros["dataLancamento"] = "Data não pode ser futura"
                    gravar_banco = False
            except ValueError:
                validacao_campos_erros["dataLancamento"] = "Data inválida"
                gravar_banco = False
        
        if gravar_banco:
            try:
                atividade_antiga_id = lancamento.atividade_id
                
                lancamento.atividade_id = atividade_id
                lancamento.usuario_id = usuario_id
                lancamento.data_lancamento = data_lancamento_obj
                lancamento.descricao = descricao
                lancamento.horas_gastas = horas_processadas
                
                db.session.commit()
                
                # Recalcula horas das atividades afetadas
                lancamento.atualizar_horas_atividade()
                if atividade_antiga_id != int(atividade_id):
                    # Se mudou de atividade, recalcula a atividade antiga também
                    total_horas_antiga = LancamentoHorasModel.calcular_total_horas_atividade(atividade_antiga_id)
                    atividade_antiga = AtividadeModel.query.get(atividade_antiga_id)
                    if atividade_antiga:
                        atividade_antiga.horas_utilizadas = total_horas_antiga
                        db.session.commit()
                
                flash(("Lançamento de horas atualizado com sucesso!", "success"))
                return redirect(url_for("lancamento_horas_listar"))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao atualizar lançamento: {str(e)}", "error"))
                gravar_banco = False
    
    # Prepara dados corretos para preencher o formulário
    if request.method == "POST" and not gravar_banco:
        dados_corretos = request.form
    else:
        dados_corretos = {
            'atividadeId': str(lancamento.atividade_id),
            'usuarioId': str(lancamento.usuario_id),
            'dataLancamento': lancamento.data_lancamento.strftime('%Y-%m-%d'),
            'descricao': lancamento.descricao,
            'horasGastas': str(lancamento.horas_gastas).replace('.', ',')
        }
    
    return render_template(
        "sistema_wr/gerenciar/projetos/lancamento_horas_editar.html",
        lancamento=lancamento,
        projetos=projetos,
        atividades=atividades,
        usuarios=usuarios,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )


@app.route("/gerenciar/lancamento-horas/excluir/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def lancamento_horas_excluir(id):
    lancamento = LancamentoHorasModel.obter_lancamento_por_id(id)
    if not lancamento:
        flash(("Lançamento não encontrado!", "warning"))
        return redirect(url_for("lancamento_horas_listar"))
    
    try:
        # método delete customizado que atualiza automaticamente as horas da atividade
        lancamento.delete()
        
        flash(("Lançamento de horas excluído com sucesso!", "success"))
        
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao excluir lançamento: {str(e)}", "error"))
    
    return redirect(url_for("lancamento_horas_listar"))


@app.route("/api/atividades-por-projeto/<int:projeto_id>")
@login_required
@requires_roles
def obter_atividades_por_projeto(projeto_id):
    """API para obter atividades de um projeto específico (para AJAX)"""
    atividades = AtividadeModel.listar_atividades_por_projeto(projeto_id)
    
    atividades_json = []
    for atividade in atividades:
        atividades_json.append({
            'id': atividade.id,
            'titulo': atividade.titulo,
            'horas_necessarias': atividade.horas_necessarias,
            'horas_utilizadas': atividade.horas_utilizadas
        })
    
    return jsonify({
        'success': True,
        'atividades': atividades_json
    })

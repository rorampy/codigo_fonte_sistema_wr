from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_prioridade_model import PrioridadeAtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_andamento_model import AndamentoAtividadeModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from datetime import datetime


@app.route("/kanban")
@app.route("/kanban/<int:projeto_id>")
@login_required
@requires_roles
def kanban_visualizar(projeto_id=None):
    filtro_projeto = request.args.get('projeto_id', projeto_id)
    filtro_responsavel = request.args.get('responsavel_id')
    filtro_situacao = request.args.get('situacao_id')
    filtro_prioridade = request.args.get('prioridade_id')
    filtro_titulo = request.args.get('titulo')
    modo_visualizacao = request.args.get('modo', 'prioridade')
    
    # Persiste modo na sessão
    if modo_visualizacao in ['prioridade', 'situacao']:
        session['kanban_modo'] = modo_visualizacao
    else:
        modo_visualizacao = session.get('kanban_modo', 'prioridade')
    
    projetos = ProjetoModel.query.filter(
        ProjetoModel.deletado == False,
        ProjetoModel.ativo == True
    ).order_by(ProjetoModel.nome_projeto.asc()).all()
    
    # Projeto atual
    # Projeto atual
    projeto_atual = None
    if filtro_projeto:
        try:
            filtro_projeto = int(filtro_projeto)
            projeto_atual = ProjetoModel.query.filter(
                ProjetoModel.id == filtro_projeto,
                ProjetoModel.deletado == False
            ).first()
        except (ValueError, TypeError):
            filtro_projeto = None
            projeto_atual = None
    
    # Dados para filtros
    prioridades = PrioridadeAtividadeModel.listar_prioridades_ativas()
    andamentos = AndamentoAtividadeModel.listar_andamentos_ativos()
    usuarios = UsuarioModel.query.filter(
        UsuarioModel.deletado == False,
        UsuarioModel.ativo == True
    ).order_by(UsuarioModel.nome.asc()).all()
    
    # Organiza atividades
    atividades_organizadas = {}
    
    query = AtividadeModel.query.filter(AtividadeModel.deletado == False)

    # Se tem projeto específico selecionado, filtra por ele
    if filtro_projeto:
        query = query.filter(AtividadeModel.projeto_id == filtro_projeto)

    if filtro_responsavel:
        query = query.filter(AtividadeModel.usuario_execucao_id == filtro_responsavel)

    if filtro_situacao and modo_visualizacao == 'prioridade':
        query = query.filter(AtividadeModel.situacao_id == filtro_situacao)

    if filtro_prioridade and modo_visualizacao == 'situacao':
        query = query.filter(AtividadeModel.prioridade_id == filtro_prioridade)

    if filtro_titulo:
        query = query.filter(AtividadeModel.titulo.ilike(f"%{filtro_titulo}%"))

    atividades = query.order_by(AtividadeModel.data_cadastro.desc()).all()

    # Organiza por modo
    if modo_visualizacao == 'prioridade':
        for prioridade in prioridades:
            atividades_organizadas[prioridade.id] = [
                a for a in atividades if a.prioridade_id == prioridade.id
            ]
    else:
        for andamento in andamentos:
            atividades_organizadas[andamento.id] = [
                a for a in atividades if a.situacao_id == andamento.id
            ]
    
    # Define colunas
    colunas = prioridades if modo_visualizacao == 'prioridade' else andamentos
    tipo_coluna = modo_visualizacao
    
    return render_template(
        "sistema_wr/gerenciar/projetos/kanban.html",
        projetos=projetos,
        projeto_atual=projeto_atual,
        colunas=colunas,
        tipo_coluna=tipo_coluna,
        atividades_organizadas=atividades_organizadas,
        prioridades=prioridades,
        andamentos=andamentos,
        usuarios=usuarios,
        modo_visualizacao=modo_visualizacao,
        filtros={
            'projeto_id': filtro_projeto,
            'responsavel_id': filtro_responsavel,
            'situacao_id': filtro_situacao,
            'prioridade_id': filtro_prioridade,
            'titulo': filtro_titulo,
            'modo': modo_visualizacao
        }
    )


@app.route("/kanban/atualizar_prioridade", methods=["POST"])
@login_required
@requires_roles
def kanban_atualizar_prioridade():
    """
    Atualiza prioridade via drag and drop
    """
    try:
        data = request.get_json()
        atividade_id = int(data.get('atividade_id'))
        nova_prioridade_id = int(data.get('nova_prioridade_id'))
        
        # Busca atividade
        atividade = AtividadeModel.query.filter(
            AtividadeModel.id == atividade_id,
            AtividadeModel.deletado == False
        ).first()
        
        if not atividade:
            return jsonify({'success': False, 'message': 'Atividade não encontrada'})
        
        # Busca prioridade
        prioridade = PrioridadeAtividadeModel.obter_prioridade_por_id(nova_prioridade_id)
        if not prioridade:
            return jsonify({'success': False, 'message': 'Prioridade não encontrada'})

        atividade.prioridade_id = nova_prioridade_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Prioridade alterada para {prioridade.nome}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@app.route("/kanban/atualizar_situacao", methods=["POST"])
@login_required
@requires_roles
def kanban_atualizar_situacao():
    """
    Atualiza situação via drag and drop
    """
    try:
        data = request.get_json()
        atividade_id = int(data.get('atividade_id'))
        nova_situacao_id = int(data.get('nova_situacao_id'))
        
        # Busca atividade
        atividade = AtividadeModel.query.filter(
            AtividadeModel.id == atividade_id,
            AtividadeModel.deletado == False
        ).first()
        
        if not atividade:
            return jsonify({'success': False, 'message': 'Atividade não encontrada'})
        
        # Busca situação
        situacao = AndamentoAtividadeModel.obter_andamento_por_id(nova_situacao_id)
        if not situacao:
            return jsonify({'success': False, 'message': 'Situação não encontrada'})
        
        # Validação especial para conclusão
        if nova_situacao_id == 4:  # Concluída
            from sistema.models_views.sistema_wr.gerenciar.projetos.lancamento_horas_model import LancamentoHorasModel
            
            lancamentos = LancamentoHorasModel.query.filter(
                LancamentoHorasModel.atividade_id == atividade_id,
                LancamentoHorasModel.deletado == False
            ).count()
            
            if lancamentos == 0:
                return jsonify({
                    'success': False, 
                    'message': 'Atividade precisa ter horas lançadas para ser concluída'
                })
        
        atividade.situacao_id = nova_situacao_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Situação alterada para {situacao.nome}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@app.route("/kanban/filtrar", methods=["GET"])
@login_required
@requires_roles
def kanban_filtrar():
    projeto_id = request.args.get('projeto_id')
    responsavel_id = request.args.get('responsavel_id')
    situacao_id = request.args.get('situacao_id')
    prioridade_id = request.args.get('prioridade_id')
    titulo = request.args.get('titulo')
    modo = request.args.get('modo', 'prioridade')
    
    # Constroe URL com filtros
    params = []
    if responsavel_id:
        params.append(f'responsavel_id={responsavel_id}')
    if situacao_id:
        params.append(f'situacao_id={situacao_id}')
    if prioridade_id:
        params.append(f'prioridade_id={prioridade_id}')
    if titulo:
        params.append(f'titulo={titulo}')
    if modo:
        params.append(f'modo={modo}')
    
    # URL final
    base_url = url_for('kanban_visualizar', projeto_id=projeto_id) if projeto_id else url_for('kanban_visualizar')
    
    if params:
        final_url = f"{base_url}?{'&'.join(params)}"
    else:
        final_url = base_url
    
    return redirect(final_url)


@app.route("/kanban/detalhes/<int:atividade_id>")
@login_required
@requires_roles
def kanban_detalhes_atividade(atividade_id):
    atividade = AtividadeModel.query.filter(
        AtividadeModel.id == atividade_id,
        AtividadeModel.deletado == False
    ).first()
    
    if not atividade:
        return jsonify({'success': False, 'message': 'Atividade não encontrada'})
    
    return jsonify({
        'success': True,
        'atividade': {
            'id': atividade.id,
            'titulo': atividade.titulo,
            'descricao': atividade.descricao,
            'projeto': {
                'id': atividade.projeto.id,
                'nome': atividade.projeto.nome_projeto
            },
            'prioridade': {
                'id': atividade.prioridade.id,
                'nome': atividade.prioridade.nome
            },
            'situacao': {
                'id': atividade.situacao.id,
                'nome': atividade.situacao.nome
            },
            'responsavel': {
                'id': atividade.usuario_execucao.id if atividade.usuario_execucao else None,
                'nome': atividade.usuario_execucao.nome if atividade.usuario_execucao else 'Não atribuído'
            },
            'horas': {
                'necessarias': atividade.horas_necessarias,
                'utilizadas': atividade.horas_utilizadas,
                'percentual': atividade.percentual_horas
            },
            'valor': f"R$ {atividade.valor_atividade_100 / 100:.2f}".replace('.', ',') if atividade.valor_atividade_100 else "R$ 0,00",
            'prazo': atividade.data_prazo_conclusao.strftime('%d/%m/%Y') if atividade.data_prazo_conclusao else None,
            'atrasada': atividade.esta_atrasada,
            'anexos': atividade.anexos.filter_by(deletado=False).count(),
            'criado_em': atividade.data_cadastro.strftime('%d/%m/%Y %H:%M') if atividade.data_cadastro else None
        }
    })

from sistema import app, requires_roles, db, current_user
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from sistema.models_views.sistema_wr.configuracoes.area_atividades.area_atividade_model import AreaModel

from logs_sistema import flask_logger


@app.route('/configuracoes/areas', methods=['GET'])
@login_required
@requires_roles
def areas_atividades_listar():
    """
    Lista todas as areas ativas.
    """
    areas = AreaModel.listar_areas_ativas()
    cores_permitidas = AreaModel.CORES_PERMITIDAS
    
    return render_template(
        'sistema_wr/configuracao/cadastro_area/area_listar.html',
        areas=areas,
        cores_permitidas=cores_permitidas,
        AreaModel=AreaModel
    )


@app.route('/configuracoes/areas/cadastrar', methods=['POST'])
@login_required
@requires_roles
def areas_atividades_cadastrar():
    """
    Cadastra uma nova area via AJAX.
    """
    try:
        # Obter dados do formulário
        nome = request.form.get('nome', '').strip()
        cor = request.form.get('cor', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        # Validações
        if not nome:
            return jsonify({'sucesso': False, 'mensagem': 'Nome é obrigatório'}), 400
        
        if len(nome) > 100:
            return jsonify({'sucesso': False, 'mensagem': 'Nome deve ter no máximo 100 caracteres'}), 400
        
        if not cor:
            return jsonify({'sucesso': False, 'mensagem': 'Cor é obrigatória'}), 400
        
        if not AreaModel.validar_cor(cor):
            return jsonify({'sucesso': False, 'mensagem': 'Cor inválida'}), 400
        
        if not AreaModel.validar_nome_unico(nome):
            return jsonify({'sucesso': False, 'mensagem': 'Já existe uma area com este nome'}), 400
        
        if descricao and len(descricao) > 255:
            return jsonify({'sucesso': False, 'mensagem': 'Descrição deve ter no máximo 255 caracteres'}), 400
        
        # Criar area
        area = AreaModel(
            nome=nome,
            cor=cor,
            descricao=descricao if descricao else None
        )
        
        db.session.add(area)
        db.session.commit()
        
        flask_logger.info(f"area '{nome}' cadastrada por {current_user.nome} (ID: {current_user.id})")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'area "{nome}" cadastrada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao cadastrar area: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao cadastrar area: {str(e)}'
        }), 500


@app.route('/configuracoes/areas/editar/<int:id>', methods=['POST'])
@login_required
@requires_roles
def areas_atividades_editar(id):
    """
    Edita uma area existente via AJAX.
    """
    try:
        # Buscar area
        area = AreaModel.obter_area_por_id(id)
        if not area:
            return jsonify({'sucesso': False, 'mensagem': 'area não encontrada'}), 404
        
        # Obter dados do formulário
        nome = request.form.get('nome', '').strip()
        cor = request.form.get('cor', '').strip()
        descricao = request.form.get('descricao', '').strip()
        
        # Validações
        if not nome:
            return jsonify({'sucesso': False, 'mensagem': 'Nome é obrigatório'}), 400
        
        if len(nome) > 100:
            return jsonify({'sucesso': False, 'mensagem': 'Nome deve ter no máximo 100 caracteres'}), 400
        
        if not cor:
            return jsonify({'sucesso': False, 'mensagem': 'Cor é obrigatória'}), 400
        
        if not AreaModel.validar_cor(cor):
            return jsonify({'sucesso': False, 'mensagem': 'Cor inválida'}), 400
        
        if not AreaModel.validar_nome_unico(nome, id):
            return jsonify({'sucesso': False, 'mensagem': 'Já existe uma area com este nome'}), 400
        
        if descricao and len(descricao) > 255:
            return jsonify({'sucesso': False, 'mensagem': 'Descrição deve ter no máximo 255 caracteres'}), 400
        
        # Atualizar area
        area.nome = nome
        area.cor = cor
        area.descricao = descricao if descricao else None
        
        db.session.commit()
        
        flask_logger.info(f"area ID {id} editada para '{nome}' por {current_user.nome} (ID: {current_user.id})")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'area "{nome}" atualizada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao editar area ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao editar area: {str(e)}'
        }), 500


@app.route('/configuracoes/areas/contar-vinculadas/<int:id>', methods=['GET'])
@login_required
@requires_roles
def areas_atividades_contar_vinculadas(id):
    """
    Retorna o número de solicitações e atividades vinculadas a uma area.
    """
    try:
        area = AreaModel.obter_area_por_id(id)
        if not area:
            return jsonify({'sucesso': False, 'mensagem': 'area não encontrada'}), 404
        
        total_solicitacoes = AreaModel.contar_solicitacoes_vinculadas(id)
        total_atividades = AreaModel.contar_atividades_vinculadas(id)
        
        return jsonify({
            'sucesso': True,
            'total': total_solicitacoes + total_atividades,
            'total_solicitacoes': total_solicitacoes,
            'total_atividades': total_atividades,
            'area_nome': area.nome
        })
        
    except Exception as e:
        flask_logger.error(f"Erro ao contar vínculos da area ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao contar vínculos: {str(e)}'
        }), 500


@app.route('/configuracoes/areas/deletar/<int:id>', methods=['POST'])
@login_required
@requires_roles
def areas_atividades_deletar(id):
    """
    Deleta uma area (soft delete) e desvincula todas as solicitações.
    """
    try:
        area = AreaModel.obter_area_por_id(id)
        if not area:
            return jsonify({'sucesso': False, 'mensagem': 'area não encontrada'}), 404
        
        nome_area = area.nome
        
        # Desvincular todas as solicitações
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
        
        solicitacoes = SolicitacaoAtividadeModel.query.filter_by(
            area_id=id,
            deletado=False
        ).all()

        atividades = AtividadeModel.query.filter_by(
            area_id=id,
            deletado=False
        ).all()
        
        for solicitacao in solicitacoes:
            solicitacao.area_id = None
        
        for atividade in atividades:
            atividade.area_id = None
        
        # Soft delete da area
        area.deletado = True
        
        db.session.commit()
        
        flask_logger.info(f"area ID {id} ('{nome_area}') deletada por {current_user.nome} (ID: {current_user.id}). {len(solicitacoes)} solicitações desvinculadas.")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'area "{nome_area}" excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao deletar area ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao deletar area: {str(e)}'
        }), 500


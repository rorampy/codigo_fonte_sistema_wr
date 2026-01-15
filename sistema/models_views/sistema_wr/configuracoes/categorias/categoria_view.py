from sistema import app, requires_roles, db, current_user
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from sistema.models_views.sistema_wr.configuracoes.categorias.categoria_model import CategoriaModel

from logs_sistema import flask_logger


@app.route('/configuracoes/categorias', methods=['GET'])
@login_required
@requires_roles
def categorias_listar():
    """
    Lista todas as categorias ativas.
    """
    categorias = CategoriaModel.listar_categorias_ativas()
    cores_permitidas = CategoriaModel.CORES_PERMITIDAS
    
    return render_template(
        'sistema_wr/configuracao/cadastro_categoria/categoria_listar.html',
        categorias=categorias,
        cores_permitidas=cores_permitidas,
        CategoriaModel=CategoriaModel
    )


@app.route('/configuracoes/categorias/cadastrar', methods=['POST'])
@login_required
@requires_roles
def categoria_cadastrar():
    """
    Cadastra uma nova categoria via AJAX.
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
        
        if not CategoriaModel.validar_cor(cor):
            return jsonify({'sucesso': False, 'mensagem': 'Cor inválida'}), 400
        
        if not CategoriaModel.validar_nome_unico(nome):
            return jsonify({'sucesso': False, 'mensagem': 'Já existe uma categoria com este nome'}), 400
        
        if descricao and len(descricao) > 255:
            return jsonify({'sucesso': False, 'mensagem': 'Descrição deve ter no máximo 255 caracteres'}), 400
        
        # Criar categoria
        categoria = CategoriaModel(
            nome=nome,
            cor=cor,
            descricao=descricao if descricao else None
        )
        
        db.session.add(categoria)
        db.session.commit()
        
        flask_logger.info(f"Categoria '{nome}' cadastrada por {current_user.nome} (ID: {current_user.id})")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Categoria "{nome}" cadastrada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao cadastrar categoria: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao cadastrar categoria: {str(e)}'
        }), 500


@app.route('/configuracoes/categorias/editar/<int:id>', methods=['POST'])
@login_required
@requires_roles
def categoria_editar(id):
    """
    Edita uma categoria existente via AJAX.
    """
    try:
        # Buscar categoria
        categoria = CategoriaModel.obter_categoria_por_id(id)
        if not categoria:
            return jsonify({'sucesso': False, 'mensagem': 'Categoria não encontrada'}), 404
        
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
        
        if not CategoriaModel.validar_cor(cor):
            return jsonify({'sucesso': False, 'mensagem': 'Cor inválida'}), 400
        
        if not CategoriaModel.validar_nome_unico(nome, id):
            return jsonify({'sucesso': False, 'mensagem': 'Já existe uma categoria com este nome'}), 400
        
        if descricao and len(descricao) > 255:
            return jsonify({'sucesso': False, 'mensagem': 'Descrição deve ter no máximo 255 caracteres'}), 400
        
        # Atualizar categoria
        categoria.nome = nome
        categoria.cor = cor
        categoria.descricao = descricao if descricao else None
        
        db.session.commit()
        
        flask_logger.info(f"Categoria ID {id} editada para '{nome}' por {current_user.nome} (ID: {current_user.id})")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Categoria "{nome}" atualizada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao editar categoria ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao editar categoria: {str(e)}'
        }), 500


@app.route('/configuracoes/categorias/contar-vinculadas/<int:id>', methods=['GET'])
@login_required
@requires_roles
def categoria_contar_vinculadas(id):
    """
    Retorna o número de solicitações e atividades vinculadas a uma categoria.
    """
    try:
        categoria = CategoriaModel.obter_categoria_por_id(id)
        if not categoria:
            return jsonify({'sucesso': False, 'mensagem': 'Categoria não encontrada'}), 404
        
        total_solicitacoes = CategoriaModel.contar_solicitacoes_vinculadas(id)
        total_atividades = CategoriaModel.contar_atividades_vinculadas(id)
        
        return jsonify({
            'sucesso': True,
            'total': total_solicitacoes + total_atividades,
            'total_solicitacoes': total_solicitacoes,
            'total_atividades': total_atividades,
            'categoria_nome': categoria.nome
        })
        
    except Exception as e:
        flask_logger.error(f"Erro ao contar vínculos da categoria ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao contar vínculos: {str(e)}'
        }), 500


@app.route('/configuracoes/categorias/deletar/<int:id>', methods=['POST'])
@login_required
@requires_roles
def categoria_deletar(id):
    """
    Deleta uma categoria (soft delete) e desvincula todas as solicitações.
    """
    try:
        categoria = CategoriaModel.obter_categoria_por_id(id)
        if not categoria:
            return jsonify({'sucesso': False, 'mensagem': 'Categoria não encontrada'}), 404
        
        nome_categoria = categoria.nome
        
        # Desvincular todas as solicitações
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
        
        solicitacoes = SolicitacaoAtividadeModel.query.filter_by(
            categoria_id=id,
            deletado=False
        ).all()

        atividades = AtividadeModel.query.filter_by(
            categoria_id=id,
            deletado=False
        ).all()
        
        for solicitacao in solicitacoes:
            solicitacao.categoria_id = None
        
        for atividade in atividades:
            atividade.categoria_id = None
        
        # Soft delete da categoria
        categoria.deletado = True
        
        db.session.commit()
        
        flask_logger.info(f"Categoria ID {id} ('{nome_categoria}') deletada por {current_user.nome} (ID: {current_user.id}). {len(solicitacoes)} solicitações desvinculadas.")
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Categoria "{nome_categoria}" excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f"Erro ao deletar categoria ID {id}: {str(e)}")
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao deletar categoria: {str(e)}'
        }), 500


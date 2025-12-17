from sistema import app, requires_roles, db, current_user
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema.models_views.sistema_wr.configuracoes.tags.tags_model import TagModel
from logs_sistema import flask_logger


@app.route('/tags/cadastrar', methods=['GET', 'POST'])
@login_required
@requires_roles
def tags_cadastrar():
    """
    Exibe formulário de cadastro de tag (GET) ou processa criação (POST).
    """
    

    if request.method == 'POST':
        # Dicts para validação (padrão do projeto)
        campos_obrigatorios = {}
        campos_erros = {}
        dados_corretos = {}

        # Capturar dados do formulário
        nome = request.form.get('nome', '').strip()
        cor = request.form.get('cor', '').strip()
        descricao = request.form.get('descricao', '').strip()

        # ==================== VALIDAÇÕES ====================
        
        # Validar nome (obrigatório)
        if not nome:
            campos_obrigatorios['nome'] = 'O nome da tag é obrigatório.'
        elif len(nome) > 100:
            campos_erros['nome'] = 'O nome deve ter no máximo 100 caracteres.'
        elif not TagModel.validar_nome_unico(nome):
            campos_erros['nome'] = 'Já existe uma tag com esse nome.'
        else:
            dados_corretos['nome'] = nome

        # Validar cor (obrigatória e deve estar na lista)
        if not cor:
            campos_obrigatorios['cor'] = 'A cor da tag é obrigatória.'
        elif cor not in TagModel.CORES_PERMITIDAS:
            campos_erros['cor'] = 'Cor inválida. Selecione uma das opções disponíveis.'
        else:
            dados_corretos['cor'] = cor

        # Descrição (opcional, sem validação)
        if descricao:
            dados_corretos['descricao'] = descricao

        # ==================== SE HOUVER ERROS, RETORNAR FORMULÁRIO ====================
        if campos_obrigatorios or campos_erros:
            return render_template(
                'sistema_wr/configuracao/cadastro_tags/tags_cadastrar.html',
                cores_permitidas=TagModel.CORES_PERMITIDAS,
                TagModel=TagModel,  
                campos_obrigatorios=campos_obrigatorios,
                campos_erros=campos_erros,
                dados_corretos=dados_corretos
            )

        # ==================== SALVAR NO BANCO ====================
        try:
            nova_tag = TagModel(
                nome=dados_corretos['nome'],
                cor=dados_corretos['cor'],
                descricao=dados_corretos.get('descricao')
            )
            db.session.add(nova_tag)
            db.session.commit()

            flask_logger.info(f"Tag '{dados_corretos['nome']}' cadastrada com sucesso por usuário {current_user.nome} (ID: {current_user.id}).")
            flash(('Tag cadastrada com sucesso!', 'success'))
            return redirect(url_for('tags_listar'))

        except Exception as e:
            db.session.rollback()
            flask_logger.error(f"Erro ao cadastrar tag '{dados_corretos.get('nome', 'N/A')}': {str(e)}")
            flash(('Ocorreu um erro ao cadastrar a tag. Tente novamente.', 'danger'))
            return redirect(url_for('tags_cadastrar'))

    # ==================== GET: RENDERIZAR FORMULÁRIO VAZIO ====================
    return render_template(
        'sistema_wr/configuracao/cadastro_tags/tags_cadastrar.html',
        cores_permitidas=TagModel.CORES_PERMITIDAS,
        TagModel=TagModel,  
        campos_obrigatorios={},
        campos_erros={},
        dados_corretos={}
    )



# ==================== LISTAR TAGS ====================
@app.route('/tags/listar', methods=['GET'])
@login_required
@requires_roles
def tags_listar():
    """
    Exibe a lista de tags cadastradas.
    """
    tags = TagModel.listar_tags_ativas()
    return render_template('sistema_wr/configuracao/cadastro_tags/tags_listar.html', 
                         tags=tags,
                         cores_permitidas=TagModel.CORES_PERMITIDAS,
                         TagModel=TagModel)
                         


# ==================== EDITAR TAG ====================
@app.route('/tags/editar/<int:tag_id>', methods=['POST'])
@login_required
@requires_roles
def tags_editar(tag_id):
    """
    Edita uma tag existente (via AJAX).
    
    Args:
        tag_id (int): ID da tag a ser editada
        
    Returns:
        JSON com sucesso/erro
    """

    tag = TagModel.obter_tag_por_id(tag_id)
    if not tag:
        return jsonify({'sucesso': False, 'mensagem': 'Tag não encontrada.'}), 404

    nome = request.form.get('nome', '').strip()
    cor = request.form.get('cor', '').strip()
    descricao = request.form.get('descricao', '').strip()

    # Validações
    if not nome:
        return jsonify({'sucesso': False, 'mensagem': 'Nome é obrigatório.'}), 400

    if len(nome) > 100:
        return jsonify({'sucesso': False, 'mensagem': 'Nome não pode ultrapassar 100 caracteres.'}), 400

    if not TagModel.validar_nome_unico(nome, tag_id=tag_id):
        return jsonify({'sucesso': False, 'mensagem': 'Já existe outra tag com esse nome.'}), 400

    if cor not in TagModel.CORES_PERMITIDAS:
        return jsonify({'sucesso': False, 'mensagem': 'Cor inválida. Selecione uma opção válida.'}), 400

    try:
        tag.nome = nome
        tag.cor = cor
        tag.descricao = descricao if descricao else None
        db.session.commit()
        
        flash(('Tag editada com sucesso!', 'success'))

        flask_logger.info(f'Tag ID {tag_id} editada para "{nome}" por {current_user.nome} (ID: {current_user.id}).')
        return jsonify({'sucesso': True, 'mensagem': 'Tag editada com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f'Erro ao editar tag ID {tag_id}: {e}')
        return jsonify({'sucesso': False, 'mensagem': 'Erro ao editar tag.'}), 500


# ==================== DELETAR TAG ====================
@app.route('/tags/deletar/<int:tag_id>', methods=['POST'])
@login_required
@requires_roles
def tags_deletar(tag_id):
    """
    Deleta (exclusão lógica) uma tag existente (via AJAX).
    
    Args:
        tag_id (int): ID da tag a ser deletada
        
    Returns:
        JSON com sucesso/erro
    """

    tag = TagModel.obter_tag_por_id(tag_id)
    if not tag:
        return jsonify({'sucesso': False, 'mensagem': 'Tag não encontrada.'}), 404

    try:
        tag.deletado = True
        db.session.commit()
        
        flask_logger.info(f'Tag ID {tag_id} ("{tag.nome}") deletada por {current_user.nome} (ID: {current_user.id}).')
        return jsonify({'sucesso': True, 'mensagem': 'Tag deletada com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        flask_logger.error(f'Erro ao deletar tag ID {tag_id}: {e}')
        return jsonify({'sucesso': False, 'mensagem': 'Erro ao deletar tag.'}), 500
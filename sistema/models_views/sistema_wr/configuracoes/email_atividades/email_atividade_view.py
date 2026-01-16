# email_atividade_view.py
from sistema import app, db, requires_roles
from flask import render_template, request, jsonify
from flask_login import login_required
from sistema.models_views.sistema_wr.configuracoes.email_atividades.email_atividade_model import EmailAtividadeModel
from sistema._utilitarios.processador_variaveis_email_atividade import ProcessadorVariaveisEmailAtividade

@app.route('/configuracoes/email-atividades', methods=['GET'])
@login_required
@requires_roles
def email_atividades_gerenciar():
    """Tela única para gerenciar todos os templates de e-mail"""
    
    # Buscar templates existentes (ou criar vazios se não existirem)
    templates = {}
    for tipo, descricao in EmailAtividadeModel.TIPOS_EVENTO:
        # Buscar template independente do status ativo
        template = EmailAtividadeModel.obter_por_tipo_evento(tipo, apenas_ativos=False)
        if not template:
            # Criar objeto temporário para exibição (não salvo no banco)
            template = EmailAtividadeModel(
                tipo_evento=tipo,
                descricao_evento=descricao,
                assunto='',
                corpo_email='',
                ativo=False
            )
        templates[tipo] = template
    
    # Obter variáveis disponíveis por tipo
    variaveis = ProcessadorVariaveisEmailAtividade.obter_todas_variaveis()
    
    return render_template(
        'sistema_wr/configuracao/email_atividades/email_atividades_gerenciar.html',
        templates=templates,
        variaveis=variaveis
    )


@app.route('/configuracoes/email-atividades/salvar/<tipo_evento>', methods=['POST'])
@login_required
@requires_roles
def email_atividades_salvar(tipo_evento):
    """Salva/atualiza um template específico via AJAX"""

    try:
        dados = request.get_json()
        


        # Validações
        if not EmailAtividadeModel.validar_tipo_evento(tipo_evento):
            return jsonify({'success': False, 'message': 'Tipo de evento inválido!'}), 400
        
        assunto = dados.get('assunto', '').strip()
        corpo_email = dados.get('corpo_email', '').strip()
        ativo = dados.get('ativo', False)
        
        if not assunto:
            return jsonify({'success': False, 'message': 'Assunto é obrigatório!'}), 400
        
        if not corpo_email:
            return jsonify({'success': False, 'message': 'Corpo do e-mail é obrigatório!'}), 400
        
        # Buscar ou criar template
        template = EmailAtividadeModel.obter_por_tipo_evento(tipo_evento, apenas_ativos=False)
        
        if template:
            # Atualizar existente
            template.assunto = assunto
            template.corpo_email = corpo_email
            template.ativo = ativo
        else:
            # Criar novo
            descricao = dict(EmailAtividadeModel.TIPOS_EVENTO).get(tipo_evento, tipo_evento)
            template = EmailAtividadeModel(
                tipo_evento=tipo_evento,
                descricao_evento=descricao,
                assunto=assunto,
                corpo_email=corpo_email,
                ativo=ativo
            )
            db.session.add(template)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Template salvo com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar: {str(e)}'
        }), 500
    

@app.route('/configuracoes/email-atividades/preview/<tipo_evento>', methods=['POST'])
@login_required
@requires_roles
def email_atividades_preview(tipo_evento):
    """Gera preview do template com variáveis substituídas por valores de exemplo"""
    try:
        dados = request.get_json()
        assunto = dados.get('assunto', '')
        corpo = dados.get('corpo_email', '')
        
        # Dados de exemplo por tipo de evento
        dados_exemplo = {
            'solicitacao_criada': {
                'SOLICITANTE_NOME': 'João Silva',
                'SOLICITANTE_EMAIL': 'joao.silva@empresa.com',
                'SOLICITACAO_ID': '123',
                'SOLICITACAO_TITULO': 'Implementar nova funcionalidade',
                'SOLICITACAO_DESCRICAO': 'Desenvolver módulo de relatórios',
                'PROJETO_NOME': 'Sistema de Gestão',
                'PRAZO_RESPOSTA_DIAS': '5',
                'DATA_LIMITE': '21/01/2026',
                'DATA_SOLICITACAO': '16/01/2026',
                'CATEGORIA_NOME': 'Desenvolvimento',
                'LINK_SOLICITACAO': 'http://sistema.com/solicitacoes/123'
            },
            'solicitacao_aceita': {
                'SOLICITANTE_NOME': 'João Silva',
                'SOLICITANTE_EMAIL': 'joao.silva@empresa.com',
                'SOLICITACAO_ID': '123',
                'SOLICITACAO_TITULO': 'Implementar nova funcionalidade',
                'PROJETO_NOME': 'Sistema de Gestão',
                'ATIVIDADE_ID': '456',
                'ATIVIDADE_TITULO': 'Desenvolver módulo de relatórios',
                'DATA_ACEITACAO': '16/01/2026',
                'LINK_ATIVIDADE': 'http://sistema.com/atividades/456',
                'LINK_SOLICITACAO': 'http://sistema.com/solicitacoes/123'
            },
            'solicitacao_rejeitada': {
                'SOLICITANTE_NOME': 'João Silva',
                'SOLICITANTE_EMAIL': 'joao.silva@empresa.com',
                'SOLICITACAO_ID': '123',
                'SOLICITACAO_TITULO': 'Implementar nova funcionalidade',
                'PROJETO_NOME': 'Sistema de Gestão',
                'MOTIVO_REJEICAO': 'Fora do escopo atual do projeto',
                'USUARIO_REJEITOU': 'Maria Santos',
                'DATA_REJEICAO': '16/01/2026',
                'TOTAL_REJEICOES': '1',
                'LINK_EDITAR': 'http://sistema.com/solicitacoes/123/editar'
            },
            'atividade_concluida': {
                'SOLICITANTE_NOME': 'João Silva',
                'SOLICITANTE_EMAIL': 'joao.silva@empresa.com',
                'ATIVIDADE_ID': '456',
                'ATIVIDADE_TITULO': 'Desenvolver módulo de relatórios',
                'PROJETO_NOME': 'Sistema de Gestão',
                'DATA_CONCLUSAO': '16/01/2026',
                'RESPONSAVEL_NOME': 'Carlos Oliveira',
                'LINK_ATIVIDADE': 'http://sistema.com/atividades/456'
            }
        }
        
        # Obter variáveis de exemplo para o tipo
        variaveis_exemplo = dados_exemplo.get(tipo_evento, {})
        
        # Substituir variáveis no assunto (simples, sem formatação de links)
        assunto_preview = assunto
        for var, valor in variaveis_exemplo.items():
            assunto_preview = assunto_preview.replace(f'[{var}]', valor)
        
        # Substituir variáveis no corpo usando o método do processador
        # para manter consistência com os links formatados como botões
        corpo_preview = ProcessadorVariaveisEmailAtividade.substituir_variaveis_preview(
            texto=corpo,
            variaveis=variaveis_exemplo
        )
        
        # Renderizar HTML do e-mail com o template
        email_html = ProcessadorVariaveisEmailAtividade.renderizar_email_html(
            assunto=assunto_preview,
            corpo=corpo_preview,
            tipo_evento=tipo_evento
        )
        
        return jsonify({
            'success': True,
            'assunto': assunto_preview,
            'corpo': corpo_preview,
            'html': email_html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar preview: {str(e)}'
        }), 500
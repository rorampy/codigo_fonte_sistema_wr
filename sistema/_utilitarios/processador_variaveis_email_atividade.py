from sistema._utilitarios import *
from datetime import datetime, timedelta
from flask import url_for


class ProcessadorVariaveisEmailAtividade:
    """
    Classe responsável por processar e substituir variáveis nos templates de e-mail de atividades.
    Padrão de variáveis: [NOME_VARIAVEL]
    """
    
    # Lista de variáveis disponíveis por tipo de evento
    VARIAVEIS_DISPONIVEIS = {
        'solicitacao_criada': [
            'SOLICITANTE_NOME', 'SOLICITANTE_EMAIL', 'SOLICITACAO_ID', 'SOLICITACAO_TITULO',
            'SOLICITACAO_DESCRICAO', 'PROJETO_NOME', 'PRAZO_RESPOSTA_DIAS', 'DATA_LIMITE',
            'DATA_SOLICITACAO', 'CATEGORIA_NOME', 'LINK_SOLICITACAO'
        ],
        'solicitacao_aceita': [
            'SOLICITANTE_NOME', 'SOLICITANTE_EMAIL', 'SOLICITACAO_ID', 'SOLICITACAO_TITULO',
            'PROJETO_NOME', 'ATIVIDADE_ID', 'ATIVIDADE_TITULO', 'DATA_ACEITACAO',
            'LINK_ATIVIDADE', 'LINK_SOLICITACAO'
        ],
        'solicitacao_rejeitada': [
            'SOLICITANTE_NOME', 'SOLICITANTE_EMAIL', 'SOLICITACAO_ID', 'SOLICITACAO_TITULO',
            'PROJETO_NOME', 'MOTIVO_REJEICAO', 'USUARIO_QUE_REJEITOU', 'DATA_REJEICAO',
            'TOTAL_REJEICOES', 'LINK_EDITAR'
        ],
        'atividade_concluida': [
            'SOLICITANTE_NOME', 'SOLICITANTE_EMAIL', 'ATIVIDADE_ID', 'ATIVIDADE_TITULO',
            'PROJETO_NOME', 'DATA_CONCLUSAO', 'RESPONSAVEL_NOME', 'LINK_ATIVIDADE'
        ]
    }
    
    @staticmethod
    def substituir_variaveis(texto, solicitacao=None, atividade=None, usuario_acao=None):
        """
        Substitui as variáveis no texto pelos valores correspondentes.
        
        Args:
            texto: Template de e-mail com variáveis [NOME_VARIAVEL]
            solicitacao: Objeto SolicitacaoAtividadeModel (opcional)
            atividade: Objeto AtividadeModel (opcional)
            usuario_acao: Usuário que executou a ação (ex: quem rejeitou)
        
        Returns:
            Texto com variáveis substituídas
        """
        if not texto:
            return texto
        
        variaveis = {}
        
        # ========== Variáveis da SOLICITAÇÃO ==========
        if solicitacao:
            # Dados básicos da solicitação
            variaveis['SOLICITACAO_ID'] = str(solicitacao.id)
            variaveis['SOLICITACAO_TITULO'] = solicitacao.titulo or ''
            variaveis['SOLICITACAO_DESCRICAO'] = solicitacao.descricao or ''
            
            # Dados do solicitante
            if solicitacao.usuario_solicitante:
                variaveis['SOLICITANTE_NOME'] = solicitacao.usuario_solicitante.nome +' '+ (solicitacao.usuario_solicitante.sobrenome or '')
                variaveis['SOLICITANTE_EMAIL'] = solicitacao.usuario_solicitante.email or ''
            else:
                variaveis['SOLICITANTE_NOME'] = 'Usuário não identificado'
                variaveis['SOLICITANTE_EMAIL'] = ''
            
            # Dados do projeto
            if solicitacao.projeto:
                variaveis['PROJETO_NOME'] = solicitacao.projeto.nome_projeto or ''
            else:
                variaveis['PROJETO_NOME'] = 'Projeto não especificado'
            
            # Prazo de resposta
            variaveis['PRAZO_RESPOSTA_DIAS'] = str(solicitacao.prazo_resposta_dias)
            
            # Data limite para resposta (usando utilitário DataHora)
            if solicitacao.data_cadastro and solicitacao.prazo_resposta_dias:
                data_limite = DataHora.adicionar_dias_em_data(
                    solicitacao.data_cadastro, 
                    solicitacao.prazo_resposta_dias
                )
                variaveis['DATA_LIMITE'] = DataHora.converter_data_de_en_para_br(data_limite)
            else:
                variaveis['DATA_LIMITE'] = ''
            
            # Data da solicitação (usando utilitário DataHora)
            if solicitacao.data_cadastro:
                variaveis['DATA_SOLICITACAO'] = DataHora.converter_data_de_en_para_br(solicitacao.data_cadastro)
            else:
                variaveis['DATA_SOLICITACAO'] = ''
            
            # Categoria (se existir)
            if solicitacao.categoria:
                variaveis['CATEGORIA_NOME'] = solicitacao.categoria.nome or ''
            else:
                variaveis['CATEGORIA_NOME'] = 'Sem categoria'
            
            # Motivo da rejeição
            variaveis['MOTIVO_REJEICAO'] = solicitacao.motivo_rejeicao or 'Não especificado'
            
            # Total de rejeições
            try:
                variaveis['TOTAL_REJEICOES'] = str(solicitacao.obter_total_rejeicoes())
            except:
                variaveis['TOTAL_REJEICOES'] = '0'
            
            # Data de rejeição (usando utilitário DataHora)
            variaveis['DATA_REJEICAO'] = DataHora.obter_data_atual_padrao_br()
            
            # Links
            try:
                variaveis['LINK_SOLICITACAO'] = url_for('atividade_solicitacao_visualizar', id=solicitacao.id, _external=True)
                variaveis['LINK_EDITAR'] = url_for('atividade_solicitacao_editar', id=solicitacao.id, _external=True)
            except:
                # Fallback caso não esteja em contexto de request
                variaveis['LINK_SOLICITACAO'] = f'/gerenciar/solicitacoes-atividades/visualizar/{solicitacao.id}'
                variaveis['LINK_EDITAR'] = f'/gerenciar/solicitacoes-atividades/editar/{solicitacao.id}'
        
        # ========== Variáveis da ATIVIDADE ==========
        if atividade:
            variaveis['ATIVIDADE_ID'] = str(atividade.id)
            variaveis['ATIVIDADE_TITULO'] = atividade.titulo or ''
            
            # Data de conclusão (usando utilitário DataHora)
            if hasattr(atividade, 'data_conclusao') and atividade.data_conclusao:
                variaveis['DATA_CONCLUSAO'] = DataHora.converter_data_de_en_para_br(atividade.data_conclusao)
            else:
                variaveis['DATA_CONCLUSAO'] = DataHora.obter_data_atual_padrao_br()
            
            # Data de aceitação (usando utilitário DataHora)
            if hasattr(atividade, 'data_cadastro') and atividade.data_cadastro:
                variaveis['DATA_ACEITACAO'] = DataHora.converter_data_de_en_para_br(atividade.data_cadastro)
            else:
                variaveis['DATA_ACEITACAO'] = DataHora.obter_data_atual_padrao_br()
            
            # Responsável pela atividade
            if hasattr(atividade, 'desenvolvedor') and atividade.desenvolvedor:
                variaveis['RESPONSAVEL_NOME'] = atividade.desenvolvedor.nome + ' ' + (atividade.desenvolvedor.sobrenome or '') or ''
            elif hasattr(atividade, 'responsavel') and atividade.responsavel:
                variaveis['RESPONSAVEL_NOME'] = atividade.responsavel.nome + ' ' + (atividade.responsavel.sobrenome or '') or ''
            else:
                variaveis['RESPONSAVEL_NOME'] = 'Não atribuído'
            
            # Projeto da atividade
            if hasattr(atividade, 'projeto') and atividade.projeto:
                variaveis['PROJETO_NOME'] = atividade.projeto.nome_projeto or ''
            
            # Link da atividade
            try:
                variaveis['LINK_ATIVIDADE'] = url_for('atividade_visualizar', atividade_id=atividade.id, _external=True)
            except:
                variaveis['LINK_ATIVIDADE'] = f'/gerenciar/atividades/visualizar/{atividade.id}'
        
        # Fallback: extrair dados do solicitante da atividade se não veio da solicitação
        if 'SOLICITANTE_NOME' not in variaveis and hasattr(atividade, 'usuario_solicitante') and atividade.usuario_solicitante:
            variaveis['SOLICITANTE_NOME'] = atividade.usuario_solicitante.nome + ' ' + (atividade.usuario_solicitante.sobrenome or '')
            variaveis['SOLICITANTE_EMAIL'] = atividade.usuario_solicitante.email or ''


        # ========== Variáveis do USUÁRIO que executou a ação ==========
        if usuario_acao:
            variaveis['USUARIO_QUE_REJEITOU'] = usuario_acao.nome +' '+ (usuario_acao.sobrenome or 'Usuário desconhecido')
        else:
            variaveis['USUARIO_QUE_REJEITOU'] = 'Sistema'
        
        # ========== Substituição das variáveis ==========
        
        # Mapeamento de links para textos amigáveis (botões clicáveis)
        links_textos = {
            'LINK_SOLICITACAO': 'MINHA SOLICITAÇÃO',
            'LINK_ATIVIDADE': 'VER ATIVIDADE',
            'LINK_EDITAR': 'EDITAR SOLICITAÇÃO'
        }
        
        # Identificar quais links existem no texto
        links_encontrados = []
        for chave in links_textos.keys():
            if f'[{chave}]' in texto and chave in variaveis:
                valor = variaveis[chave]
                if valor and not valor.startswith('['):
                    links_encontrados.append((chave, valor, links_textos[chave]))
        
        # Se há exatamente 2 links, renderizar lado a lado
        if len(links_encontrados) == 2:
            link1, link2 = links_encontrados
            tabela_dupla = f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 15px 0;">
                <tr>
                    <td align="center" width="50%" style="padding: 0 3px;">
                        <a href="{link1[1]}" target="_blank" style="display: inline-block; padding: 10px 12px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{link1[2]}</a>
                    </td>
                    <td align="center" width="50%" style="padding: 0 3px;">
                        <a href="{link2[1]}" target="_blank" style="display: inline-block; padding: 10px 12px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{link2[2]}</a>
                    </td>
                </tr>
            </table>'''
            # Substituir o primeiro link pela tabela dupla
            texto = texto.replace(f'[{link1[0]}]', tabela_dupla)
            # Remover o segundo link (já está na tabela)
            texto = texto.replace(f'[{link2[0]}]', '')
        else:
            # Comportamento normal: cada link em bloco separado
            for chave, valor, texto_link in links_encontrados:
                link_html = f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 15px 0;">
                    <tr>
                        <td align="center">
                            <a href="{valor}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{texto_link}</a>
                        </td>
                    </tr>
                </table>'''
                texto = texto.replace(f'[{chave}]', link_html)
        
        # Substituição normal para outras variáveis (não-links)
        for chave, valor in variaveis.items():
            if chave not in links_textos:
                texto = texto.replace(f'[{chave}]', str(valor) if valor is not None else f'[{chave}]')
        
        return texto
    
    @staticmethod
    def substituir_variaveis_preview(texto, variaveis):
        """
        Substitui variáveis usando um dicionário de exemplo.
        Aplica a mesma formatação de links do método principal.
        
        Args:
            texto: Template com variáveis [NOME_VARIAVEL]
            variaveis: Dict com valores de exemplo {'VARIAVEL': 'valor'}
        
        Returns:
            Texto com variáveis substituídas e links formatados como botões
        """
        if not texto:
            return texto
        
        # Mapeamento de links para textos amigáveis (botões clicáveis)
        links_textos = {
            'LINK_SOLICITACAO': 'MINHA SOLICITAÇÃO',
            'LINK_ATIVIDADE': 'VER ATIVIDADE',
            'LINK_EDITAR': 'EDITAR SOLICITAÇÃO'
        }
        
        # Identificar quais links existem no texto
        links_encontrados = []
        for chave in links_textos.keys():
            if f'[{chave}]' in texto and chave in variaveis:
                valor = variaveis[chave]
                if valor:
                    links_encontrados.append((chave, valor, links_textos[chave]))
        
        # Se há exatamente 2 links, renderizar lado a lado
        if len(links_encontrados) == 2:
            link1, link2 = links_encontrados
            tabela_dupla = f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 15px 0;">
                <tr>
                    <td align="center" width="50%" style="padding: 0 3px;">
                        <a href="{link1[1]}" target="_blank" style="display: inline-block; padding: 10px 12px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{link1[2]}</a>
                    </td>
                    <td align="center" width="50%" style="padding: 0 3px;">
                        <a href="{link2[1]}" target="_blank" style="display: inline-block; padding: 10px 12px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{link2[2]}</a>
                    </td>
                </tr>
            </table>'''
            texto = texto.replace(f'[{link1[0]}]', tabela_dupla)
            texto = texto.replace(f'[{link2[0]}]', '')
        else:
            # Comportamento normal: cada link em bloco separado
            for chave, valor, texto_link in links_encontrados:
                link_html = f'''<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 15px 0;">
                    <tr>
                        <td align="center">
                            <a href="{valor}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #206bc4; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">{texto_link}</a>
                        </td>
                    </tr>
                </table>'''
                texto = texto.replace(f'[{chave}]', link_html)
        
        # Substituição normal para outras variáveis (não-links)
        for chave, valor in variaveis.items():
            if chave not in links_textos:
                texto = texto.replace(f'[{chave}]', str(valor) if valor is not None else f'[{chave}]')
        
        return texto
    
    @staticmethod
    def obter_variaveis_disponiveis(tipo_evento):
        """
        Retorna a lista de variáveis disponíveis para um tipo de evento.
        
        Args:
            tipo_evento: Chave do tipo de evento (ex: 'solicitacao_criada')
        
        Returns:
            Lista de variáveis disponíveis ou lista vazia se tipo inválido
        """
        return ProcessadorVariaveisEmailAtividade.VARIAVEIS_DISPONIVEIS.get(tipo_evento, [])
    
    @staticmethod
    def obter_todas_variaveis():
        """Retorna um dicionário com todas as variáveis disponíveis por tipo de evento"""
        return ProcessadorVariaveisEmailAtividade.VARIAVEIS_DISPONIVEIS
    
    @staticmethod
    def obter_exemplo_variavel(variavel):
        """Retorna um exemplo de valor para uma variável (útil para preview no CRUD)"""
        exemplos = {
            'SOLICITANTE_NOME': 'João Silva',
            'SOLICITANTE_EMAIL': 'joao.silva@email.com',
            'SOLICITACAO_ID': '123',
            'SOLICITACAO_TITULO': 'Implementar nova funcionalidade',
            'SOLICITACAO_DESCRICAO': 'Descrição detalhada da solicitação...',
            'PROJETO_NOME': 'Sistema WR',
            'PRAZO_RESPOSTA_DIAS': '7',
            'DATA_LIMITE': '23/01/2026',
            'DATA_SOLICITACAO': '16/01/2026',
            'CATEGORIA_NOME': 'Bug',
            'ATIVIDADE_ID': '456',
            'ATIVIDADE_TITULO': 'Implementar funcionalidade',
            'DATA_ACEITACAO': '17/01/2026',
            'LINK_ATIVIDADE': 'http://sistema.com/atividades/456',
            'LINK_SOLICITACAO': 'http://sistema.com/solicitacoes/123',
            'MOTIVO_REJEICAO': 'Falta de informações técnicas',
            'USUARIO_QUE_REJEITOU': 'Maria Santos',
            'DATA_REJEICAO': '18/01/2026',
            'TOTAL_REJEICOES': '1',
            'LINK_EDITAR': 'http://sistema.com/solicitacoes/123/editar',
            'DATA_CONCLUSAO': '25/01/2026',
            'RESPONSAVEL_NOME': 'Pedro Costa'
        }
        return exemplos.get(variavel, f'[{variavel}]')
    
    @staticmethod
    def obter_descricao_variavel(variavel):
        """Retorna descrição legível de cada variável (útil para UI do CRUD)"""
        descricoes = {
            'SOLICITANTE_NOME': 'Nome completo do usuário que criou a solicitação',
            'SOLICITANTE_EMAIL': 'E-mail do solicitante',
            'SOLICITACAO_ID': 'Número identificador da solicitação',
            'SOLICITACAO_TITULO': 'Título da solicitação',
            'SOLICITACAO_DESCRICAO': 'Descrição completa da solicitação',
            'PROJETO_NOME': 'Nome do projeto relacionado',
            'PRAZO_RESPOSTA_DIAS': 'Quantidade de dias para resposta',
            'DATA_LIMITE': 'Data limite para resposta (formato DD/MM/AAAA)',
            'DATA_SOLICITACAO': 'Data em que a solicitação foi criada',
            'CATEGORIA_NOME': 'Categoria da solicitação',
            'ATIVIDADE_ID': 'Número identificador da atividade',
            'ATIVIDADE_TITULO': 'Título da atividade',
            'DATA_ACEITACAO': 'Data em que a solicitação foi aceita',
            'LINK_ATIVIDADE': 'Link para visualizar a atividade',
            'LINK_SOLICITACAO': 'Link para visualizar a solicitação',
            'MOTIVO_REJEICAO': 'Motivo pelo qual a solicitação foi rejeitada',
            'USUARIO_QUE_REJEITOU': 'Nome do usuário que rejeitou',
            'DATA_REJEICAO': 'Data da rejeição',
            'TOTAL_REJEICOES': 'Quantidade total de rejeições',
            'LINK_EDITAR': 'Link para editar a solicitação',
            'DATA_CONCLUSAO': 'Data de conclusão da atividade',
            'RESPONSAVEL_NOME': 'Nome do desenvolvedor responsável'
        }
        return descricoes.get(variavel, variavel)
    
    @staticmethod
    def renderizar_email_html(assunto, corpo, tipo_evento=None):
        """
        Renderiza o template HTML do e-mail com o conteúdo processado.
        
        Args:
            assunto: Assunto do e-mail (já com variáveis substituídas)
            corpo: Corpo do e-mail (já com variáveis substituídas)
            tipo_evento: Tipo de evento (opcional, para exibir badge)
        
        Returns:
            HTML renderizado do e-mail
        """
        from flask import render_template
        from datetime import datetime
        
        # Mapear tipo_evento para descrição amigável
        tipos_descricao = {
            'solicitacao_criada': 'Nova Solicitação',
            'solicitacao_aceita': 'Solicitação Aprovada',
            'solicitacao_rejeitada': 'Solicitação Rejeitada',
            'atividade_concluida': 'Atividade Concluída'
        }
        
        # Mapear tipo_evento para classe CSS do badge
        badge_classes = {
            'solicitacao_criada': 'badge-criada',
            'solicitacao_aceita': 'badge-aceita',
            'solicitacao_rejeitada': 'badge-rejeitada',
            'atividade_concluida': 'badge-concluida'
        }
        
        tipo_evento_descricao = tipos_descricao.get(tipo_evento, None)
        badge_classe = badge_classes.get(tipo_evento, 'badge-criada')
        data_envio = DataHora.converter_data_de_en_para_br(datetime.now())
        
        # Converter quebras de linha para <br> (compatibilidade com Outlook)
        corpo_html = corpo.replace('\n', '<br>') if corpo else ''
        
        return render_template(
            'relatorio_layout/email_atividades_layout/email_atividades.html',
            assunto=assunto,
            corpo=corpo_html,
            tipo_evento_descricao=tipo_evento_descricao,
            badge_classe=badge_classe,
            data_envio=data_envio
        )
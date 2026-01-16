from sistema import db
from sistema.models_views.base_model import BaseModel


class EmailAtividadeModel(BaseModel):
    __tablename__ = 'z_sys_email_atividade'

    # Constante de tipos de evento
    TIPOS_EVENTO = [
        ('solicitacao_criada', 'Solicitação de Atividade Criada'),
        ('solicitacao_aceita', 'Solicitação de Atividade Aceita'),
        ('solicitacao_rejeitada', 'Solicitação de Atividade Rejeitada'),
        ('atividade_concluida', 'Atividade Concluída')
    ]

    id = db.Column(db.Integer, primary_key=True)
    tipo_evento = db.Column(db.String(50), nullable=False, unique=True)  # Tipo de evento (único)
    descricao_evento = db.Column(db.String(100), nullable=False)  # Descrição do evento
    assunto = db.Column(db.String(255), nullable=False)  # Assunto do email
    corpo_email = db.Column(db.Text, nullable=False)  # Corpo do email (HTML com variáveis)
    ativo = db.Column(db.Boolean, nullable=False, default=True)  # Indica se o template está ativo

    def __init__(self, tipo_evento, descricao_evento, assunto, corpo_email, ativo=True):
        self.tipo_evento = tipo_evento
        self.descricao_evento = descricao_evento
        self.assunto = assunto
        self.corpo_email = corpo_email
        self.ativo = ativo

    @staticmethod
    def listar_todos():
        """Retorna todos os templates de email (não deletados), ordenados por tipo_evento"""
        return EmailAtividadeModel.query.filter_by(deletado=False).order_by(EmailAtividadeModel.tipo_evento).all()

    @staticmethod
    def listar_ativos():
        """Retorna apenas templates ativos (não deletados e ativo=True)"""
        return EmailAtividadeModel.query.filter_by(deletado=False, ativo=True).order_by(EmailAtividadeModel.tipo_evento).all()

    @staticmethod
    def obter_por_id(template_id):
        """Retorna template por ID (se não deletado)"""
        return EmailAtividadeModel.query.filter_by(id=template_id, deletado=False).first()

    @staticmethod
    def obter_por_tipo_evento(tipo, apenas_ativos=True):
        """
        Retorna template para um tipo de evento específico.
        Se apenas_ativos=True, retorna apenas ativos (usado no disparo de emails).
        Se apenas_ativos=False, retorna qualquer um (usado na tela de configuração).
        """
        if apenas_ativos:
            return EmailAtividadeModel.query.filter_by(tipo_evento=tipo, ativo=True, deletado=False).first()
        else:
            return EmailAtividadeModel.query.filter_by(tipo_evento=tipo, deletado=False).first()

    @staticmethod
    def validar_tipo_evento(tipo):
        """Valida se o tipo de evento existe na constante TIPOS_EVENTO"""
        tipos_validos = [t[0] for t in EmailAtividadeModel.TIPOS_EVENTO]
        return tipo in tipos_validos

    @staticmethod
    def validar_tipo_evento_unico(tipo, id_atual=None):
        """
        Valida se o tipo_evento já existe em outro template
        Retorna True se for único (pode usar), False se já existe
        """
        query = EmailAtividadeModel.query.filter_by(tipo_evento=tipo, deletado=False)
        
        # Se for edição, excluir o próprio registro da validação
        if id_atual:
            query = query.filter(EmailAtividadeModel.id != id_atual)
        
        return query.first() is None

    @staticmethod
    def listar_tipos_disponiveis():
        """Retorna lista de tipos de evento disponíveis para cadastro"""
        tipos_cadastrados = db.session.query(EmailAtividadeModel.tipo_evento).filter_by(deletado=False).all()
        tipos_cadastrados = [t[0] for t in tipos_cadastrados]
        
        tipos_disponiveis = [
            (tipo, descricao) 
            for tipo, descricao in EmailAtividadeModel.TIPOS_EVENTO 
            if tipo not in tipos_cadastrados
        ]
        
        return tipos_disponiveis
    
    @staticmethod
    def enviar_email(tipo_evento, email_destino, solicitacao=None, atividade=None, usuario_acao=None):
        """
        Envia e-mail processado com template configurado.
        Centraliza toda a lógica: busca template, processa variáveis, renderiza HTML, dispara Huey.
        
        Args:
            tipo_evento: Chave do tipo ('solicitacao_criada', 'solicitacao_aceita', etc.)
            email_destino: Email ou lista de emails para envio
            solicitacao: Objeto SolicitacaoAtividadeModel (opcional)
            atividade: Objeto AtividadeModel (opcional)
            usuario_acao: Usuário que executou a ação (opcional)
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        from sistema._utilitarios.processador_variaveis_email_atividade import ProcessadorVariaveisEmailAtividade
        from servidor_huey.tarefas import enviar_email_html
        from logs_sistema import flask_logger
        
        try:
            # Buscar template ativo
            template = EmailAtividadeModel.obter_por_tipo_evento(tipo_evento, apenas_ativos=False)
            
            if not template or not template.ativo:
                flask_logger.info(f"Template '{tipo_evento}' inativo ou não encontrado. E-mail não enviado.")
                return {'success': False, 'message': 'Template inativo ou não encontrado'}
            
            # Processar assunto
            assunto_processado = ProcessadorVariaveisEmailAtividade.substituir_variaveis(
                texto=template.assunto,
                solicitacao=solicitacao,
                atividade=atividade,
                usuario_acao=usuario_acao
            )
            
            # Processar corpo do email
            corpo_processado = ProcessadorVariaveisEmailAtividade.substituir_variaveis(
                texto=template.corpo_email,
                solicitacao=solicitacao,
                atividade=atividade,
                usuario_acao=usuario_acao
            )
            
            # Renderizar HTML com layout
            email_html = ProcessadorVariaveisEmailAtividade.renderizar_email_html(
                assunto=assunto_processado,
                corpo=corpo_processado,
                tipo_evento=tipo_evento
            )
            
            # Suportar lista de emails
            emails_destino = email_destino if isinstance(email_destino, list) else [email_destino]
            
            # Disparar via Huey para cada destinatário
            for email in emails_destino:
                if email and email.strip():
                    enviar_email_html.schedule(
                        args=(assunto_processado, email_html, email.strip()),
                        delay=5
                    )
            
            flask_logger.info(
                f"[EMAIL] '{tipo_evento}' agendado para {len(emails_destino)} destinatário(s) "
                f"(Solicitação: {solicitacao.id if solicitacao else 'N/A'}, "
                f"Atividade: {atividade.id if atividade else 'N/A'})"
            )
            
            return {'success': True, 'message': f'E-mail agendado para {len(emails_destino)} destinatário(s)'}
            
        except Exception as e:
            flask_logger.error(f"Erro ao enviar email '{tipo_evento}': {str(e)}")
            return {'success': False, 'message': f'Erro: {str(e)}'}



    def __repr__(self):
        return f'<EmailAtividadeModel {self.tipo_evento} - {self.descricao_evento}>'
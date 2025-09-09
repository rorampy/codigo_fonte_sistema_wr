from sistema.models_views.base_model import BaseModel, db
from datetime import datetime


class SolicitacaoAtividadeModel(BaseModel):
    """
    Model para solicitações de atividades
    """
    __tablename__ = 'proj_solicitacao_atividade'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('proj_projeto.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text(length=4294967295), nullable=True)
    situacao_id = db.Column(db.Integer, db.ForeignKey('z_sys_andamento_atividade.id'), nullable=False, default=7)  # 7 = Em Análise
    usuario_solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    motivo_rejeicao = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    projeto = db.relationship('ProjetoModel', backref='proj_solicitacao_atividade')
    usuario_solicitante = db.relationship('UsuarioModel', backref='solicitacoes_atividade')
    situacao = db.relationship('AndamentoAtividadeModel', backref='proj_solicitacao_atividade')
    anexos = db.relationship('SolicitacaoAtividadeAnexoModel', backref='proj_solicitacao_atividade', lazy='dynamic',
                            primaryjoin="and_(SolicitacaoAtividadeModel.id==SolicitacaoAtividadeAnexoModel.solicitacao_id, "
                                       "SolicitacaoAtividadeAnexoModel.deletado==False)")
    
    
    def __init__(self, projeto_id, titulo, descricao, usuario_solicitante_id, situacao_id=7):
        self.projeto_id = projeto_id
        self.titulo = titulo
        self.descricao = descricao
        self.usuario_solicitante_id = usuario_solicitante_id
        self.situacao_id = situacao_id
    
    
    @staticmethod
    def listar_solicitacoes():
        """Lista todas as solicitações de atividades ordenadas por data de cadastro"""
        return SolicitacaoAtividadeModel.query.filter(
            SolicitacaoAtividadeModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeModel.data_cadastro.desc()
        ).all()
    
    
    @staticmethod
    def listar_solicitacoes_por_usuario(usuario_id):
        """Lista solicitações de um usuário específico"""
        return SolicitacaoAtividadeModel.query.filter(
            SolicitacaoAtividadeModel.usuario_solicitante_id == usuario_id,
            SolicitacaoAtividadeModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeModel.data_cadastro.desc()
        ).all()
    
    
    @staticmethod
    def obter_solicitacao_por_id(id):
        """Obtém uma solicitação pelo ID"""
        return SolicitacaoAtividadeModel.query.filter(
            SolicitacaoAtividadeModel.id == id,
            SolicitacaoAtividadeModel.deletado == False
        ).first()
    
    
    @staticmethod
    def filtrar_solicitacoes(projeto_id=None, situacao_id=None, usuario_id=None, titulo=None):
        """Filtra solicitações com base nos parâmetros fornecidos"""
        query = SolicitacaoAtividadeModel.query.filter(
            SolicitacaoAtividadeModel.deletado == False
        )
        
        if projeto_id:
            query = query.filter(SolicitacaoAtividadeModel.projeto_id == projeto_id)
        
        if situacao_id:
            query = query.filter(SolicitacaoAtividadeModel.situacao_id == situacao_id)
        
        if usuario_id:
            query = query.filter(SolicitacaoAtividadeModel.usuario_solicitante_id == usuario_id)
        
        if titulo:
            query = query.filter(SolicitacaoAtividadeModel.titulo.ilike(f'%{titulo}%'))
        
        return query.order_by(SolicitacaoAtividadeModel.data_cadastro.desc()).all()

    def obter_total_rejeicoes(self):
        """
        Obtém o total de rejeições desta solicitação através do histórico
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_historico_model import SolicitacaoAtividadeHistoricoRejeicaoModel
        
        return SolicitacaoAtividadeHistoricoRejeicaoModel.contar_rejeicoes_por_solicitacao(self.id)


    def obter_historico_rejeicoes(self):
        """
        Obtém o histórico completo de rejeições desta solicitação
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_historico_model import SolicitacaoAtividadeHistoricoRejeicaoModel
        
        return SolicitacaoAtividadeHistoricoRejeicaoModel.listar_historico_por_solicitacao(self.id)


    def obter_ultima_rejeicao(self):
        """
        Obtém a última rejeição desta solicitação
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_historico_model import SolicitacaoAtividadeHistoricoRejeicaoModel
        
        return SolicitacaoAtividadeHistoricoRejeicaoModel.obter_ultima_rejeicao(self.id)

class SolicitacaoAtividadeAnexoModel(BaseModel):
    """
    Model para anexos das solicitações de atividades
    """
    __tablename__ = 'proj_solicitacao_atividade_anexos'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('proj_solicitacao_atividade.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    tamanho = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    
    
    def __init__(self, solicitacao_id, nome_arquivo, nome_original, caminho_arquivo, tipo_arquivo, tamanho, mime_type=None):
        self.solicitacao_id = solicitacao_id
        self.nome_arquivo = nome_arquivo
        self.nome_original = nome_original
        self.caminho_arquivo = caminho_arquivo
        self.tipo_arquivo = tipo_arquivo
        self.tamanho = tamanho
        self.mime_type = mime_type
    
    
    @staticmethod
    def obter_anexo_por_id(id):
        """Obtém um anexo pelo ID"""
        return SolicitacaoAtividadeAnexoModel.query.filter(
            SolicitacaoAtividadeAnexoModel.id == id,
            SolicitacaoAtividadeAnexoModel.deletado == False
        ).first()
    
    
    @staticmethod
    def listar_anexos_por_solicitacao(solicitacao_id):
        """Lista anexos de uma solicitação específica"""
        return SolicitacaoAtividadeAnexoModel.query.filter(
            SolicitacaoAtividadeAnexoModel.solicitacao_id == solicitacao_id,
            SolicitacaoAtividadeAnexoModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeAnexoModel.data_cadastro.asc()
        ).all()
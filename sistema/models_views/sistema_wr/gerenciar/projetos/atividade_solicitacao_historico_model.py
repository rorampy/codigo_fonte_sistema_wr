from sistema.models_views.base_model import BaseModel, db
from datetime import datetime


class SolicitacaoAtividadeHistoricoRejeicaoModel(BaseModel):
    """
    Model para histórico de rejeições das solicitações de atividades
    """
    __tablename__ = 'proj_solicitacao_atividade_historico_rejeicao'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    solicitacao_id = db.Column(db.Integer, db.ForeignKey('proj_solicitacao_atividade.id'), nullable=False)
    motivo_rejeicao = db.Column(db.Text, nullable=False)
    usuario_rejeitou_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_rejeicao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    solicitacao = db.relationship('SolicitacaoAtividadeModel', backref='historico_rejeicoes')
    usuario_rejeitou = db.relationship('UsuarioModel', backref='rejeicoes_realizadas')
    
    
    def __init__(self, solicitacao_id, motivo_rejeicao, usuario_rejeitou_id):
        self.solicitacao_id = solicitacao_id
        self.motivo_rejeicao = motivo_rejeicao
        self.usuario_rejeitou_id = usuario_rejeitou_id
        self.data_rejeicao = datetime.utcnow()
    
    
    @staticmethod
    def listar_historico_por_solicitacao(solicitacao_id):
        """Lista todo o histórico de rejeições de uma solicitação específica"""
        return SolicitacaoAtividadeHistoricoRejeicaoModel.query.filter(
            SolicitacaoAtividadeHistoricoRejeicaoModel.solicitacao_id == solicitacao_id,
            SolicitacaoAtividadeHistoricoRejeicaoModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeHistoricoRejeicaoModel.data_rejeicao.desc()
        ).all()
    
    
    @staticmethod
    def contar_rejeicoes_por_solicitacao(solicitacao_id):
        """Conta quantas vezes uma solicitação foi rejeitada"""
        return SolicitacaoAtividadeHistoricoRejeicaoModel.query.filter(
            SolicitacaoAtividadeHistoricoRejeicaoModel.solicitacao_id == solicitacao_id,
            SolicitacaoAtividadeHistoricoRejeicaoModel.deletado == False
        ).count()
    
    
    @staticmethod
    def obter_primeira_rejeicao(solicitacao_id):
        """Obtém a primeira rejeição de uma solicitação"""
        return SolicitacaoAtividadeHistoricoRejeicaoModel.query.filter(
            SolicitacaoAtividadeHistoricoRejeicaoModel.solicitacao_id == solicitacao_id,
            SolicitacaoAtividadeHistoricoRejeicaoModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeHistoricoRejeicaoModel.data_rejeicao.asc()
        ).first()
    
    
    @staticmethod
    def obter_ultima_rejeicao(solicitacao_id):
        """Obtém a última rejeição de uma solicitação"""
        return SolicitacaoAtividadeHistoricoRejeicaoModel.query.filter(
            SolicitacaoAtividadeHistoricoRejeicaoModel.solicitacao_id == solicitacao_id,
            SolicitacaoAtividadeHistoricoRejeicaoModel.deletado == False
        ).order_by(
            SolicitacaoAtividadeHistoricoRejeicaoModel.data_rejeicao.desc()
        ).first()
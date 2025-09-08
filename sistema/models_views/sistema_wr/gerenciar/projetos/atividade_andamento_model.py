from sistema.models_views.base_model import BaseModel, db


class AndamentoAtividadeModel(BaseModel):
    """
    Model para andamento das atividades (Não iniciada, Em andamento, Pausada, Concluída, Cancelada)
    """
    __tablename__ = 'z_sys_andamento_atividade'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)


    def __init__(self, nome, ativo=True):
        self.nome = nome
        self.ativo = ativo


    @staticmethod
    def listar_andamentos_ativos():
        return AndamentoAtividadeModel.query.filter(
            AndamentoAtividadeModel.deletado == False,
            AndamentoAtividadeModel.ativo == True
        ).order_by(
            AndamentoAtividadeModel.id.asc()
        ).all()


    @staticmethod
    def obter_andamento_por_id(id):
        return AndamentoAtividadeModel.query.filter(
            AndamentoAtividadeModel.id == id,
            AndamentoAtividadeModel.deletado == False
        ).first()


    @staticmethod
    def obter_andamentos_asc_nome():
        return AndamentoAtividadeModel.query.filter(
            AndamentoAtividadeModel.deletado == False
        ).order_by(
            AndamentoAtividadeModel.nome.asc()
        ).all()

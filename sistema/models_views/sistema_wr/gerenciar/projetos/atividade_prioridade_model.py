from sistema.models_views.base_model import BaseModel, db


class PrioridadeAtividadeModel(BaseModel):
    """
    Model para prioridade das atividades (Baixa, Média, Alta, Urgente)
    """
    __tablename__ = 'z_sys_prioridade_atividade'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ordem = db.Column(db.Integer, nullable=False, default=0)  # Para ordenação (1=Baixa, 2=Média, 3=Alta, 4=Urgente)
    ativo = db.Column(db.Boolean, default=True, nullable=False)


    def __init__(self, nome, ordem=0, ativo=True):
        self.nome = nome
        self.ordem = ordem
        self.ativo = ativo


    @staticmethod
    def listar_prioridades_ativas():
        return PrioridadeAtividadeModel.query.filter(
            PrioridadeAtividadeModel.deletado == False,
            PrioridadeAtividadeModel.ativo == True
        ).order_by(
            PrioridadeAtividadeModel.ordem.asc()
        ).all()

    @staticmethod
    def obter_prioridades_asc_nome():
        return PrioridadeAtividadeModel.query.filter(
            PrioridadeAtividadeModel.deletado == False
        ).order_by(
            PrioridadeAtividadeModel.nome.asc()
        ).all()
        
    
    @staticmethod
    def obter_prioridade_por_id(id):
        return PrioridadeAtividadeModel.query.filter(
            PrioridadeAtividadeModel.id == id,
            PrioridadeAtividadeModel.deletado == False
        ).first()
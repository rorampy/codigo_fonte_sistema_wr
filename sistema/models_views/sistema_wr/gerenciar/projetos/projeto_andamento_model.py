from sistema.models_views.base_model import BaseModel, db


class AndamentoProjetoModel(BaseModel):
    """
    Model para andamento dos projetos (Não iniciado, Em execução, Paralisado, Concluído)
    """
    __tablename__ = 'z_sys_andamento_projeto'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)


    def __init__(self, nome, ativo=True):
        self.nome = nome
        self.ativo = ativo


    @staticmethod
    def listar_andamentos_ativos():
        return AndamentoProjetoModel.query.filter(
            AndamentoProjetoModel.deletado == False,
            AndamentoProjetoModel.ativo == True
        ).order_by(
            AndamentoProjetoModel.id.asc()
        ).all()


    @staticmethod
    def obter_andamento_por_id(id):
        return AndamentoProjetoModel.query.filter(
            AndamentoProjetoModel.id == id,
            AndamentoProjetoModel.deletado == False
        ).first()

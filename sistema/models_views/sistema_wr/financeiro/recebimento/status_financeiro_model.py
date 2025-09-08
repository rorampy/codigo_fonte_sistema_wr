from ....base_model import BaseModel, db
from sqlalchemy import and_


class StatusFinanceiroModel(BaseModel):
    """
    Model para registro de status financeiro.
    """
    __tablename__ = 'z_sys_status_financeiro'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    descricao = db.Column(db.String(50))
    ativo = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(
            self, descricao, ativo
    ):
        self.descricao = descricao
        self.ativo = ativo

    def listar_status_financeiro():
        """
        Lista todos os status financeiros ativos.
        """
        return StatusFinanceiroModel.query.filter(StatusFinanceiroModel.ativo == True).order_by(StatusFinanceiroModel.id.desc()).all()
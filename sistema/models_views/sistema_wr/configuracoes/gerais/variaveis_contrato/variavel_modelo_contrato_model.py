from .....base_model import BaseModel, db
from sqlalchemy import desc


class VariavelModeloContrato(BaseModel):
    """
    Model base para registro de variaveis de modelo de contrato
    """
    __tablename__ = 'z_sys_variavel_modelo_contrato'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    chave = db.Column(db.String(155), nullable = False)
    descricao = db.Column(db.String(155), nullable = False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(self, chave, descricao, ativo=True):
        self.chave = chave
        self.descricao = descricao
        self.ativo = ativo

    def variaveis_modelo_contrato():
        variaveis = VariavelModeloContrato.query.filter(
            VariavelModeloContrato.ativo == True,
            VariavelModeloContrato.deletado == False,
        ).order_by(
            desc(
                VariavelModeloContrato.id
            )
        ).all()

        return variaveis
        
    
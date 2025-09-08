from .....base_model import BaseModel, db
from sqlalchemy import and_, desc


class ModeloContratoModel(BaseModel):
    """
    Model base para registro do modelo de contrato
    """
    __tablename__ = 'mo_modelo_contrato'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome_modelo = db.Column(db.String(155), nullable = False)
    conteudo = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario = db.relationship('UsuarioModel', backref=db.backref('usuario_modelo', lazy=True))
    ativo = db.Column(db.Boolean, nullable=False, default=True)


    def __init__(self, nome_modelo, conteudo, usuario_id, ativo=True):
        """
        Inicializa um novo modelo de contrato.
        Args:
            nome_modelo (str): Nome do modelo de contrato.
            conteudo (str): Conteúdo do modelo (texto/template).
            usuario_id (int): ID do usuário.
            ativo (bool): Se o modelo está ativo (padrão True).
        """
        self.nome_modelo = nome_modelo
        self.conteudo = conteudo
        self.usuario_id = usuario_id
        self.ativo = ativo

    def obter_modelos_contratos_ativos():
        """
        Retorna todos os modelos de contrato ativos e não deletados.
        Returns:
            list: Lista de modelos de contrato.
        """
        contratos = ModeloContratoModel.query.filter(
            ModeloContratoModel.deletado == False,
            ModeloContratoModel.ativo == True,
        ).order_by(
            desc(
                ModeloContratoModel.id
            )
        ).all()
        return contratos
    
    def obter_modelo_contrato_ativo_por_id(id):
        """
        Retorna um modelo de contrato específico pelo ID.
        Args:
            id (int): ID do modelo de contrato.
        Returns:
            ModeloContratoModel | None: O modelo encontrado ou None.
        """
        contrato = ModeloContratoModel.query.filter(
            ModeloContratoModel.deletado == False,
            ModeloContratoModel.ativo == True,
            ModeloContratoModel.id == id
        ).first()
        return contrato

    
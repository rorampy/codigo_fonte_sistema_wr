from ....base_model import BaseModel, db
from sqlalchemy import and_


class ClienteModel(BaseModel):
    """
    Model para registro de clientes
    """
    __tablename__ = 'cli_cliente'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    fatura_via_cpf = db.Column(db.Boolean, nullable=False, default=False)
    identificacao = db.Column(db.String(200), nullable=False)
    numero_documento = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    possui_whats = db.Column(db.Boolean, default=False, nullable=False)
    endereco_rua = db.Column(db.String(255), nullable=True)
    endereco_numero = db.Column(db.String(100), nullable=True)
    endereco_bairro = db.Column(db.String(255), nullable=True)
    endereco_cep = db.Column(db.String(100), nullable=True)
    endereco_cidade = db.Column(db.String(100), nullable=True)
    endereco_estado = db.Column(db.String(100), nullable=True)
    endereco_pais = db.Column(db.String(100), nullable=True)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
        self, fatura_via_cpf, identificacao, numero_documento, email, telefone,
        possui_whats, endereco_rua=None, endereco_numero=None, endereco_bairro=None, endereco_cep=None, endereco_cidade=None, 
        endereco_estado=None, endereco_pais=None, ativo=True
    ):
        self.fatura_via_cpf = fatura_via_cpf
        self.identificacao = identificacao
        self.numero_documento = numero_documento
        self.email = email
        self.possui_whats = possui_whats
        self.endereco_rua = endereco_rua
        self.endereco_numero = endereco_numero
        self.endereco_bairro = endereco_bairro
        self.endereco_cep = endereco_cep
        self.endereco_cidade = endereco_cidade
        self.endereco_estado = endereco_estado
        self.endereco_pais = endereco_pais
        self.telefone = telefone        
        self.ativo = ativo

    def listar_clientes():
        clientes = ClienteModel.query.filter(
            ClienteModel.deletado == 0
        ).order_by(ClienteModel.id.desc()).all()

        return clientes
        
    def listar_clientes_ativos():
        clientes = ClienteModel.query.filter(
            ClienteModel.ativo == 1
        ).order_by(ClienteModel.id.desc()).all()

        return clientes
    
    def listar_clientes_inativos():
        clientes = ClienteModel.query.filter(
            ClienteModel.ativo == 0
        ).all()

        return clientes
    
    def obter_cliente_por_id(id):
        cliente = ClienteModel.query.filter(
            ClienteModel.id == id,
            ClienteModel.deletado == 0
        ).first()

        return cliente
    
    def filtrar_clientes(
        identficacao=None,
        celular=None
    ):  
        query = ClienteModel.query.filter(
            ClienteModel.deletado == False
        )

        if identficacao:
            query = query.filter(
                ClienteModel.identificacao.ilike(f"%{identficacao}%")
            )

        if celular:
            query = query.filter(
                ClienteModel.telefone.ilike(f"%{celular}%")
            )   
            
        return query.order_by(ClienteModel.id.desc()).all()
from ....base_model import BaseModel, db
from sqlalchemy import and_

class ProdutoModel(BaseModel):
    __tablename__ = 'pro_produto'
    
    # Chave primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Campos principais do produto
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Integer(), nullable=False)
    periodo = db.Column(db.Integer(), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    
    def __init__(self, descricao, valor, periodo, ativo=True):
        """
        Construtor da classe ProdutoModel
        
        Args:
            descricao (str): Descrição do produto
            valor (float): Valor do produto
            periodo (str): Período de cobrança ('mensal' ou 'anual')
            ativo (bool): Se o produto está ativo (padrão True)
            usuario_criacao (str): Usuário que criou o registro
        """
        self.descricao = descricao
        self.valor = valor
        self.periodo = periodo
        self.ativo = ativo
    

    def listar_produtos():
        return ProdutoModel.query.all()
    
    def listar_produtos_ativos():
        return ProdutoModel.query.filter_by(ativo=True).all()

    def obter_produto_id(id):
        produto = ProdutoModel.query.filter(
            ProdutoModel.id == id
        ).first()

        return produto
    
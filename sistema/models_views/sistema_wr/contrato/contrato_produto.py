from ...base_model import BaseModel, db
from .contrato_model import ContratoModel

class ContratoProduto(BaseModel):
    __tablename__ = 'con_contrato_produto'

    # Chave primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Relacionamentos
    contrato_id = db.Column(db.Integer, db.ForeignKey('con_contrato.id'), nullable=False)
    contrato = db.relationship('ContratoModel', backref=db.backref('contrato_produto', lazy=True))
    produto_id = db.Column(db.Integer, db.ForeignKey('pro_produto.id'), nullable=False)
    produto = db.relationship('ProdutoModel', backref=db.backref('produto_contrato', lazy=True))

    # Campos específicos do produto no contrato
    valor_negociado = db.Column(db.Integer, nullable=True)  # Valor negociado para o produto neste contrato
    periodo = db.Column(db.String(50), nullable=True)       # Período de cobrança do produto neste contrato
    vigencia_inicio = db.Column(db.Date, nullable=False)
    vigencia_fim = db.Column(db.Date, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    cartao_credito = db.Column(db.Boolean, default=False, nullable=True)
    nmro_parcelas = db.Column(db.Integer, nullable=True)

    def __init__(self, contrato_id, produto_id, vigencia_inicio, vigencia_fim=None, valor_negociado=None, periodo=None, observacoes=None, cartao_credito=False, nmro_parcelas=None):
        """
        Construtor da classe ContratoProduto

        Args:
            contrato_id (int): ID do contrato
            produto_id (int): ID do produto
            vigencia_inicio (date): Data de início da vigência do produto neste contrato
            vigencia_fim (date): Data de fim da vigência do produto neste contrato (opcional)
            valor_negociado (int): Valor negociado para o produto neste contrato (opcional)
            periodo (str): Período de cobrança do produto neste contrato (opcional)
            quantidade (int): Quantidade do produto neste contrato (padrão 1)
            observacoes (str): Observações específicas deste produto no contrato (opcional)
        """
        self.contrato_id = contrato_id
        self.produto_id = produto_id
        self.vigencia_inicio = vigencia_inicio
        self.vigencia_fim = vigencia_fim
        self.valor_negociado = valor_negociado
        self.periodo = periodo
        self.observacoes = observacoes
        self.cartao_credito = cartao_credito
        self.nmro_parcelas = nmro_parcelas

    def obter_contrato_por_id(contrato_id):
        return ContratoProduto.query.filter_by(contrato_id=contrato_id, deletado=False).first()

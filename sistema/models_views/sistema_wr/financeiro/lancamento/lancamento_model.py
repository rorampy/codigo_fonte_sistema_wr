from sistema import db
from sistema.models_views.base_model import BaseModel
from sqlalchemy import and_, desc

class LancamentoModel(BaseModel):
    __tablename__ = 'lan_lancamento'

    id = db.Column(db.Integer, primary_key=True)
    despesa_recorrente = db.Column(db.Boolean, nullable=False, default=False)
    # 1 - Entrada | 2 - Saída
    tipo_lancamento = db.Column(db.Integer, nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("ca_categoria_lancamento.id"), nullable=True)
    categoria = db.relationship("CategoriaLancamentoModel", foreign_keys=[categoria_id], backref=db.backref("categoria_lancamento", lazy=True))
    data_movimentacao = db.Column(db.Date, nullable=True)
    dia_movimentacao = db.Column(db.Integer, nullable=True)
    descricao = db.Column(db.String(255), nullable=False)
    valor_lancamento_100 = db.Column(db.Integer, nullable=True)
    comprovante_id = db.Column(db.Integer, db.ForeignKey('upload_arquivo.id'), nullable=True)
    comprovante = db.relationship('UploadArquivoModel', backref=db.backref('comprovante_saida', lazy=True))

    ativo = db.Column(db.Boolean, nullable=False, default=True)

    def __init__(
        self, despesa_recorrente, tipo_lancamento, categoria_id, descricao, valor_lancamento_100
        , data_movimentacao=None, dia_movimentacao=None, comprovante_id=None, ativo=True
    ):
        self.despesa_recorrente = despesa_recorrente
        self.tipo_lancamento = tipo_lancamento
        self.categoria_id = categoria_id
        self.data_movimentacao = data_movimentacao
        self.descricao = descricao
        self.valor_lancamento_100 = valor_lancamento_100
        self.comprovante_id = comprovante_id
        self.dia_movimentacao = dia_movimentacao
        self.ativo = ativo

    def lancamentos_ativos_usuario():
        lancamentos = LancamentoModel.query.filter(
            LancamentoModel.deletado == False,
            LancamentoModel.ativo == True,
        ).order_by(desc(LancamentoModel.id)).all()

        return lancamentos
    
    def obter_lancamento_usuario(id_lancamento):
        lancamento = LancamentoModel.query.filter(
            LancamentoModel.deletado == False,
            LancamentoModel.ativo == True,
            LancamentoModel.id == id_lancamento,
        ).first()

        return lancamento

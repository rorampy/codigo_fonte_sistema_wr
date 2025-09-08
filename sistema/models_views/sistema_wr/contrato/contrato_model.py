from ...base_model import BaseModel, db
from sqlalchemy import and_


class ContratoModel(BaseModel):
    __tablename__ = 'con_contrato'

    # Chave primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey('cli_cliente.id'), nullable=False)
    cliente = db.relationship('ClienteModel', backref=db.backref('cliente_contrato', lazy=True))

    # Relacionamento de modelo de contrato
    modelo_contrato_id = db.Column(db.Integer, db.ForeignKey('mo_modelo_contrato.id'), nullable=True)
    modelo_contrato = db.relationship('ModeloContratoModel', backref=db.backref('modelo_contrato', lazy=True))

    # 1 - Ativo | 2- Inativo | 3 - Cancelado
    status_contrato = db.Column(db.Integer, nullable=False)

    forma_pagamento_id = db.Column(db.Integer, db.ForeignKey('z_sys_forma_pagamento.id'), nullable=True)
    forma_pagamento = db.relationship('FormaPagamentoModel', backref=db.backref('forma_pagamento_contrato', lazy=True))

    arquivo_contrato_id = db.Column(db.Integer, db.ForeignKey("upload_arquivo.id"), nullable=True)
    arquivo_contrato = db.relationship("UploadArquivoModel", backref=db.backref("contrato_arquivo", lazy=True))
    
    observacoes = db.Column(db.Text, nullable=True)
    contrato_assinado = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, cliente_id, forma_pagamento_id, modelo_contrato_id=None, ativo=False, contrato_assinado=False, observacoes=None, status_contrato=1):
        """
        Construtor da classe ContratoModel

        Args:
            cliente_id (int): ID do cliente vinculado ao contrato
            forma_pagamento_id (int): ID da forma de pagamento vinculada ao contrato
            modelo_contrato_id (int): ID do modelo de contrato vinculado ao contrato
            ativo (bool): Se o contrato está ativo (padrão False)
            valor_contrato (int): Valor opcional
            observacoes (str): Observações gerais do contrato (opcional)
        """
        self.cliente_id = cliente_id
        self.forma_pagamento_id = forma_pagamento_id
        self.modelo_contrato_id = modelo_contrato_id
        self.contrato_assinado = contrato_assinado
        self.ativo = ativo
        self.observacoes = observacoes
        self.status_contrato = status_contrato

    def listar_contratos():
        """
        Retorna todos os contratos cadastrados, ordenados do mais recente para o mais antigo.
        
        Returns:
            list[ContratoModel]: Lista de contratos
        """
        return ContratoModel.query.order_by(ContratoModel.id.desc()).all()

    def listar_contratos_ativos():
        """
        Retorna todos os contratos ativos, ordenados do mais recente para o mais antigo.
        
        Returns:
            list[ContratoModel]: Lista de contratos ativos
        """
        return ContratoModel.query.filter(ContratoModel.ativo == True).order_by(ContratoModel.id.desc()).all()

    def obter_contrato_id(id):
        """
        Busca um contrato pelo seu ID.
        
        Args:
            id (int): ID do contrato
        Returns:
            ContratoModel | None: Contrato encontrado ou None
        """
        contrato = ContratoModel.query.filter(
            ContratoModel.id == id
        ).first()
        return contrato
    
    def obter_contrato_por_cliente_produto_contrato(cliente_id, produto_id, contrato_id):
        """
        Busca o primeiro contrato que possua o cliente, produto e modelo de contrato informados.

        Args:
            cliente_id (int): ID do cliente vinculado ao contrato
            produto_id (int): ID do produto vinculado ao contrato
            contrato_id (int): ID do modelo de contrato vinculado ao contrato

        Returns:
            ContratoModel | None: Contrato encontrado ou None
        """
        from sistema.models_views.sistema_wr.contrato.contrato_produto import ContratoProduto
        return ContratoModel.query.filter(
            ContratoModel.cliente_id == cliente_id,
            ContratoModel.contrato_produto.any(ContratoProduto.produto_id == produto_id),
            ContratoModel.modelo_contrato_id == contrato_id
        ).first()

        
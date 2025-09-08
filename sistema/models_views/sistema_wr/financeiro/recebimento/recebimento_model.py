from sistema import db
from dateutil.relativedelta import relativedelta
from sistema.models_views.base_model import BaseModel
from sistema.models_views.sistema_wr.gerenciar.clientes.cliente_model import ClienteModel
from datetime import datetime, date
from datetime import timedelta
from sqlalchemy import and_, desc

class RecebimentoModel(BaseModel):
    __tablename__ = 're_recebimento'

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('con_contrato.id'), nullable=False)
    contrato = db.relationship('ContratoModel', backref=db.backref('recebimento_contrato', lazy=True))
    contrato_produto_id = db.Column(db.Integer, db.ForeignKey('con_contrato_produto.id'), nullable=False)
    contrato_produto = db.relationship('ContratoProduto', backref=db.backref('recebimento_contrato_produto', lazy=True))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cli_cliente.id'), nullable=False)
    cliente = db.relationship('ClienteModel', backref=db.backref('recebimento_cliente', lazy=True))
    valor_a_receber = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    valor_pago = db.Column(db.Integer, nullable=True)
    status_id = db.Column(db.Integer, db.ForeignKey('z_sys_status_financeiro.id'), nullable=True)
    status = db.relationship('StatusFinanceiroModel', backref=db.backref('recebimento_status_financeiro', lazy=True))
    comprovante_id = db.Column(db.Integer, db.ForeignKey('upload_arquivo.id'), nullable=True)
    comprovante = db.relationship('UploadArquivoModel', backref=db.backref('comprovante_recebimento', lazy=True))
    categoria_lancamento_id = db.Column(db.Integer, db.ForeignKey("ca_categoria_lancamento.id"), nullable=True)
    categoria = db.relationship("CategoriaLancamentoModel", foreign_keys=[categoria_lancamento_id], backref=db.backref("categoria_recebimento", lazy=True))
    observacao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, contrato_id, contrato_produto_id, cliente_id, valor_a_receber, data_vencimento, categoria_lancamento_id=None, comprovante_id=None, status_id=None, observacao=None, ativo=True):
        """
        Inicializa um novo recebimento.
        Args:
            contrato_id (int): ID do contrato vinculado
            contrato_produto_id (int): ID do produto do contrato
            cliente_id (int): ID do cliente
            valor_a_receber (int): Valor previsto
            categoria_lancamento_id (int, opcional): ID da categoria de lançamento
            data_vencimento (date): Data de vencimento
            comprovante_id (int, opcional): ID do comprovante
            status_id (int, opcional): Status financeiro
            observacao (str, opcional): Observação
            ativo (bool, opcional): Se está ativo
        """
        self.contrato_id = contrato_id
        self.contrato_produto_id = contrato_produto_id
        self.cliente_id = cliente_id
        self.valor_a_receber = valor_a_receber
        self.data_vencimento = data_vencimento
        self.status_id = status_id
        self.categoria_lancamento_id = categoria_lancamento_id
        self.comprovante_id = comprovante_id
        self.observacao = observacao
        self.ativo = ativo

    def listar_a_receber_agrupado_por_cliente():
        """
        Lista os recebimentos agrupados por cliente, ordenando por data de vencimento.

        - Busca todos os recebimentos ativos no sistema.
        - Agrupa os recebimentos pelo campo de identificação do cliente.
        - Para cada cliente, calcula o total a receber e lista os recebimentos dos últimos 30 dias.
        - Os recebimentos são ordenados pela data de vencimento (do mais recente para o mais antigo).

        Retorno:
            dict: {
                cliente_identificacao: {
                    'total_a_receber': int,
                    'recebimentos': [RecebimentoModel, ...]  # apenas dos últimos 30 dias
                },
                ...
            }
        """
        hoje = date.today()
        trinta_dias_atras = hoje - timedelta(days=30)

        # Consulta todos os recebimentos ativos, ordenando por data de vencimento
        recebimentos = db.session.query(
            RecebimentoModel,
            ClienteModel.identificacao
        ).join(ClienteModel, RecebimentoModel.cliente_id == ClienteModel.id
        ).filter(RecebimentoModel.ativo == True)
        recebimentos = recebimentos.order_by(RecebimentoModel.data_vencimento.desc()).all()

        agrupado = {}
        for receb, cliente in recebimentos:
            if cliente not in agrupado:
                agrupado[cliente] = {'total_a_receber': 0, 'recebimentos': []}
            agrupado[cliente]['total_a_receber'] += receb.valor_a_receber
            # Últimos 30 dias
            if trinta_dias_atras <= receb.data_vencimento <= hoje:
                agrupado[cliente]['recebimentos'].append(receb)
        return agrupado

    def buscar_recebimentos_por_contrato(contrato_id):
        """
        Busca todos os recebimentos de um contrato.
        """
        return RecebimentoModel.query.filter(RecebimentoModel.contrato_id==contrato_id, RecebimentoModel.ativo==True).all()

    def buscar_recebimentos_pendentes(cliente_id=None):
        """
        Busca recebimentos pendentes, opcionalmente filtrando por cliente.
        """
        query = RecebimentoModel.query.filter(RecebimentoModel.valor_pago == None, RecebimentoModel.ativo == True)
        if cliente_id:
            query = query.filter_by(cliente_id=cliente_id)
        return query.all()

    def gerar_recebimentos_contrato_periodo(contrato, contrato_produto, cliente, produto, valor_parcela):
        """
        Gera recebimentos automáticos conforme o período do produto (mensal/anual).
        Se anual, gera apenas um recebimento na data de início.
        Se mensal, gera um recebimento para cada mês entre início e fim da vigência.
        Args:
            contrato: objeto contrato com vigencia_inicio e vigencia_fim
            cliente: objeto cliente
            produto: objeto produto com campo periodo ('mensal' ou 'anual')
            valor_parcela: valor de cada parcela
        Returns:
            List[RecebimentoModel]: lista de recebimentos gerados
        """
        print('entrei aqui')
        data_inicio = contrato_produto.vigencia_inicio
        data_fim = contrato_produto.vigencia_fim

        if isinstance(data_inicio, str):
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        if isinstance(data_fim, str):
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

        periodo = produto.periodo  # 'mensal' ou 'anual'

        recebimentos = []

        if periodo == 1:
            receb = RecebimentoModel(
                contrato_id=contrato.id,
                contrato_produto_id=contrato_produto.id,
                cliente_id=cliente.id,
                valor_a_receber=valor_parcela,
                data_vencimento=data_inicio,
                status_id=5,
                ativo=True
            )
            db.session.add(receb)
            db.session.flush()
            recebimentos.append(receb)
            db.session.commit()
        elif periodo == 0:
            data_vencimento = data_inicio
            while data_vencimento <= data_fim:
                receb = RecebimentoModel(
                    contrato_id=contrato.id,
                    contrato_produto_id=contrato_produto.id,
                    cliente_id=cliente.id,
                    valor_a_receber=valor_parcela,
                    data_vencimento=data_vencimento,
                    status_id=5,
                    ativo=True
                )
                db.session.add(receb)
                db.session.flush()
                recebimentos.append(receb)
                db.session.commit()
                data_vencimento += relativedelta(months=1)
        return recebimentos

    def obter_recebimento_por_id(id):
        """
        Obtém um recebimento pelo seu ID.
        """
        return RecebimentoModel.query.filter(RecebimentoModel.id == id, RecebimentoModel.ativo == True).first()
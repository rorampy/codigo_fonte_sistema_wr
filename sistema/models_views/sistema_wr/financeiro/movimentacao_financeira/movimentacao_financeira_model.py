from ....base_model import BaseModel, db
from sistema.models_views.sistema_wr.gerenciar.clientes.cliente_model import ClienteModel
from sistema.models_views.sistema_wr.financeiro.lancamento.lancamento_model import LancamentoModel
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sqlalchemy import desc
from datetime import date, timedelta

class MovimentacaoFinanceiraModel(BaseModel):
    """
    Model para aguardar as movimentações financeiras
    """
    __tablename__ = 'mov_movimentacao_financeira'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    # 1 - Entrada | 2 - Saída | 3 - Cancelamento | 4 - Estorno
    tipo_movimentacao = db.Column(db.Integer, nullable=False)

    lancamento_id = db.Column(db.Integer, db.ForeignKey('lan_lancamento.id'), nullable=True)
    lancamento = db.relationship('LancamentoModel', backref=db.backref('lancamento_movimentacao', lazy=True))

    recebimento_id = db.Column(db.Integer, db.ForeignKey('re_recebimento.id'), nullable=True)
    recebimento = db.relationship('RecebimentoModel', backref=db.backref('recebimento_movimentacao', lazy=True))

    cliente_id = db.Column(db.Integer, db.ForeignKey('cli_cliente.id'), nullable=True)
    cliente = db.relationship('ClienteModel', backref=db.backref('cliente_movimentacao', lazy=True))

    valor_movimentacao_100 = db.Column(db.Integer, nullable=True)

    data_movimentacao = db.Column(db.Date, nullable=False)

    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(
            self, tipo_movimentacao, valor_movimentacao_100, data_movimentacao, ativo=True, lancamento_id=None,
            recebimento_id=None, cliente_id=None
    ):
        self.tipo_movimentacao = tipo_movimentacao
        self.data_movimentacao = data_movimentacao
        self.valor_movimentacao_100 = valor_movimentacao_100
        self.lancamento_id = lancamento_id
        self.recebimento_id = recebimento_id
        self.cliente_id = cliente_id
        self.ativo = ativo
    

    def obter_movimentacao_por_usuario_lancamento(id_lancamento):
        movimentacao = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.lancamento_id == id_lancamento
        ).first()

        return movimentacao

    def obter_valor_total_saldo_entradas_por_usuario():
        saldo = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 1 # Entrada
        ).all()

        return sum(
            s.valor_movimentacao_100
            for s in saldo
        ) or 0


    def obter_valor_total_saldo_saidas_por_usuario():
        # Retorna o total de saídas, incluindo também cancelamentos e estornos
        saldo = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.tipo_movimentacao.in_([2, 3, 4]) # 2: Saída, 3: Cancelamento, 4: Estorno
        ).all()

        return sum(
            s.valor_movimentacao_100
            for s in saldo
        ) or 0
    
    def obter_valor_total_saldo_cancelamentos_por_usuario():
        saldo = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 3 # Cancelamento
        ).all()

        return sum(
            s.valor_movimentacao_100
            for s in saldo
        ) or 0
    
    def obter_valor_total_saldo_estornos_por_usuario():
        saldo = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.deletado == 0,
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.tipo_movimentacao == 4 # Estorno
        ).all()

        return sum(
            s.valor_movimentacao_100
            for s in saldo
        ) or 0
    
    def obter_valor_total_saldo_liquido_por_usuario():
        entradas = MovimentacaoFinanceiraModel.obter_valor_total_saldo_entradas_por_usuario()
        saidas = MovimentacaoFinanceiraModel.obter_valor_total_saldo_saidas_por_usuario()

        return entradas - saidas
    
    def listagem_movimentacoes_financeiras_por_usuario():
        movimentacoes = MovimentacaoFinanceiraModel.query.filter(
            MovimentacaoFinanceiraModel.ativo == 1,
            MovimentacaoFinanceiraModel.deletado == 0,
        ).order_by(
            desc(MovimentacaoFinanceiraModel.id)
        ).all()

        return movimentacoes

    def cadastrar_movimentacao_financeira(tipo_movimentacao, valor_movimentacao, data_movimentacao, lancamento_id=None, recebimento_id=None):
        movimentacao = MovimentacaoFinanceiraModel(
            tipo_movimentacao=tipo_movimentacao,
            valor_movimentacao_100=valor_movimentacao,
            data_movimentacao=data_movimentacao,
            lancamento_id=lancamento_id,
            recebimento_id=recebimento_id
        )
        db.session.add(movimentacao)
        db.session.commit()

        return True

    def listagem_movimentacoes_financeiras_com_filtros(filtros):
        """
        Lista movimentações financeiras do usuário aplicando filtros
        """
        print(filtros)
        query = MovimentacaoFinanceiraModel.query.filter_by(
            ativo=True,
            deletado=False
        )
        
        if 'data_inicio' in filtros:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao >= filtros['data_inicio'])
        
        if 'data_fim' in filtros:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao <= filtros['data_fim'])
        
        if 'tipo_movimentacao' in filtros:
            query = query.filter(MovimentacaoFinanceiraModel.tipo_movimentacao == filtros['tipo_movimentacao'])
        
        if 'valor_minimo' in filtros:
            query = query.filter(MovimentacaoFinanceiraModel.valor_movimentacao_100 >= filtros['valor_minimo'])
        
        if 'valor_maximo' in filtros:
            query = query.filter(MovimentacaoFinanceiraModel.valor_movimentacao_100 <= filtros['valor_maximo'])
        
        if 'cliente_nome' in filtros:
            query = query.join(
                ClienteModel, 
                MovimentacaoFinanceiraModel.cliente_id == ClienteModel.id, 
                isouter=True
            ).filter(
                ClienteModel.identificacao.ilike(f"%{filtros['cliente_nome']}%")
            )
        
        if 'categoria_id' in filtros:
            query = query.join(
                LancamentoModel, 
                MovimentacaoFinanceiraModel.lancamento_id == LancamentoModel.id, 
                isouter=True
            ).filter(
                LancamentoModel.categoria_id == filtros['categoria_id']
            )
        
        return query.order_by(MovimentacaoFinanceiraModel.data_movimentacao.desc()).all()
    
    def filtrar_movimentacao_financeira(data_inicio, data_fim):
        if not data_inicio or not data_fim:
            data_inicio = date.today()-timedelta(days=30)
            data_fim = date.today()
        
        query = db.session.query(MovimentacaoFinanceiraModel).filter(MovimentacaoFinanceiraModel.ativo == True)
        
        
        if data_inicio and data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao.between(data_inicio, data_fim))
        elif data_inicio:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao >= data_inicio)
        elif data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao <= data_fim)
        
        return query.order_by(desc(MovimentacaoFinanceiraModel.id)).all()
    
    def filtrar_movimentacao_financeira_saldo_entrada(data_inicio, data_fim):
        if not data_inicio or not data_fim:
            data_inicio = date.today()-timedelta(days=30)
            data_fim = date.today()
        
        query = db.session.query(MovimentacaoFinanceiraModel).filter(MovimentacaoFinanceiraModel.ativo == True,
                                                                     MovimentacaoFinanceiraModel.tipo_movimentacao == 1)

        if data_inicio and data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao.between(data_inicio, data_fim))
        elif data_inicio:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao >= data_inicio)
        elif data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao <= data_fim)
        
        return sum(
            q.valor_movimentacao_100
            for q in query ) or 0
    
    def filtrar_movimentacao_financeira_saldo_saida(data_inicio, data_fim):
        if not data_inicio or not data_fim:
            data_inicio = date.today()-timedelta(days=30)
            data_fim = date.today()

        query = db.session.query(MovimentacaoFinanceiraModel).filter(MovimentacaoFinanceiraModel.ativo == True,
                                                                     MovimentacaoFinanceiraModel.tipo_movimentacao.in_([2, 3, 4]))
        if data_inicio and data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao.between(data_inicio, data_fim))
        elif data_inicio:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao >= data_inicio)
        elif data_fim:
            query = query.filter(MovimentacaoFinanceiraModel.data_movimentacao <= data_fim)

        return sum(
            q.valor_movimentacao_100
            for q in query ) or 0
    
    def filtrar_movimentacao_financeira_liquido(data_inicio, data_fim):
        entradas = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira_saldo_entrada(data_inicio=data_inicio, data_fim=data_fim)
        saidas = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira_saldo_saida(data_inicio=data_inicio, data_fim=data_fim)

        return entradas - saidas          
        
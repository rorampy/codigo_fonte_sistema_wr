from sistema.models_views.base_model import BaseModel, db


class LancamentoHorasModel(BaseModel):
    """
    Model para lançamento de horas gastas em atividades
    """
    __tablename__ = 'proj_lancamento_horas'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    atividade_id = db.Column(db.Integer, db.ForeignKey('proj_atividade.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_lancamento = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    horas_gastas = db.Column(db.Float, nullable=False)
    
    # Relacionamentos
    atividade = db.relationship('AtividadeModel', backref='proj_lancamentos_horas')
    usuario = db.relationship('UsuarioModel', backref='proj_lancamentos_horas')
    
    
    def __init__(self, atividade_id, usuario_id, data_lancamento, descricao, horas_gastas):
        self.atividade_id = atividade_id
        self.usuario_id = usuario_id
        self.data_lancamento = data_lancamento
        self.descricao = descricao
        self.horas_gastas = horas_gastas
    
    
    @staticmethod
    def listar_lancamentos_por_atividade(atividade_id):
        """Lista todos os lançamentos de uma atividade específica"""
        return LancamentoHorasModel.query.filter(
            LancamentoHorasModel.atividade_id == atividade_id,
            LancamentoHorasModel.deletado == False
        ).order_by(LancamentoHorasModel.data_lancamento.desc()).all()
    
    
    @staticmethod
    def listar_lancamentos_por_usuario(usuario_id, data_inicio=None, data_fim=None):
        """Lista lançamentos de um usuário específico, opcionalmente filtrado por período"""
        query = LancamentoHorasModel.query.filter(
            LancamentoHorasModel.usuario_id == usuario_id,
            LancamentoHorasModel.deletado == False
        )
        
        if data_inicio:
            query = query.filter(LancamentoHorasModel.data_lancamento >= data_inicio)
        if data_fim:
            query = query.filter(LancamentoHorasModel.data_lancamento <= data_fim)
            
        return query.order_by(LancamentoHorasModel.data_lancamento.desc()).all()
    
    
    @staticmethod
    def obter_lancamento_por_id(id):
        """Obtém um lançamento específico por ID"""
        return LancamentoHorasModel.query.filter(
            LancamentoHorasModel.id == id,
            LancamentoHorasModel.deletado == False
        ).first()
    
    
    @staticmethod
    def calcular_total_horas_atividade(atividade_id):
        """Calcula o total de horas lançadas para uma atividade"""
        result = db.session.query(
            db.func.sum(LancamentoHorasModel.horas_gastas)
        ).filter(
            LancamentoHorasModel.atividade_id == atividade_id,
            LancamentoHorasModel.deletado == False
        ).scalar()
        
        return result or 0.0
    
    
    @staticmethod
    def filtrar_lancamentos(atividade_id=None, usuario_id=None, data_inicio=None, data_fim=None):
        """Filtra lançamentos com múltiplos critérios"""
        query = LancamentoHorasModel.query.filter(
            LancamentoHorasModel.deletado == False
        )
        
        if atividade_id:
            query = query.filter(LancamentoHorasModel.atividade_id == atividade_id)
        if usuario_id:
            query = query.filter(LancamentoHorasModel.usuario_id == usuario_id)
        if data_inicio:
            query = query.filter(LancamentoHorasModel.data_lancamento >= data_inicio)
        if data_fim:
            query = query.filter(LancamentoHorasModel.data_lancamento <= data_fim)
            
        return query.order_by(LancamentoHorasModel.data_lancamento.desc()).all()
    
    
    def atualizar_horas_atividade(self):
        """Atualiza o campo horas_utilizadas da atividade relacionada"""
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
        
        atividade = AtividadeModel.query.get(self.atividade_id)
        if atividade:
            total_horas = self.calcular_total_horas_atividade(self.atividade_id)
            atividade.horas_utilizadas = total_horas
            return True
        return False
    
    
    @property
    def horas_formatadas(self):
        """Retorna as horas formatadas como string"""
        return f"{self.horas_gastas:.2f}h"
    
    
    @property
    def data_formatada(self):
        """Retorna a data formatada para exibição"""
        return self.data_lancamento.strftime('%d/%m/%Y')
    
    
    def save(self):
        """Override do save para atualizar automaticamente as horas da atividade"""
        db.session.add(self)
        db.session.flush()  # Para obter o ID
        self.atualizar_horas_atividade()
        db.session.commit()
        return self
    
    
    def delete(self):
        """Override do delete para atualizar as horas da atividade após exclusão"""
        self.deletado = True
        db.session.flush()
        self.atualizar_horas_atividade()
        db.session.commit()

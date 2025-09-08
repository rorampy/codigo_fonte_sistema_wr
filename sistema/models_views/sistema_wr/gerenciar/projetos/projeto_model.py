from ....base_model import BaseModel, db
from sqlalchemy import and_, or_
from datetime import datetime


# Tabela intermediária para many-to-many entre Projeto e Usuario
projeto_usuario_associacao = db.Table(
    'proj_projeto_usuario',
    db.Column('projeto_id', db.Integer, db.ForeignKey('proj_projeto.id'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('data_associacao', db.DateTime, default=datetime.utcnow)
)


class ProjetoModel(BaseModel):
    """
    Model para gerenciamento de projetos
    """
    __tablename__ = 'proj_projeto'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    nome_projeto = db.Column(db.String(200), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=True)
    
    # Responsável técnico (um único usuário)
    responsavel_tecnico_id = db.Column(
        db.Integer, 
        db.ForeignKey("usuario.id"), 
        nullable=False
    )
    
    responsavel_tecnico = db.relationship(
        "UsuarioModel",
        foreign_keys=[responsavel_tecnico_id],
        backref=db.backref("projetos_responsavel", lazy=True)
    )
    
    # Usuários envolvidos (many-to-many)
    usuarios_envolvidos = db.relationship(
        "UsuarioModel",
        secondary=projeto_usuario_associacao,
        backref=db.backref("projetos_participacao", lazy=True)
    )
    
    observacoes = db.Column(db.Text, nullable=True)
    
    # Andamento do projeto
    andamento_id = db.Column(
        db.Integer,
        db.ForeignKey("z_sys_andamento_projeto.id"),
        nullable=False
    )
    andamento = db.relationship(
        "AndamentoProjetoModel",
        backref=db.backref("projetos", lazy=True)
    )
    
    ativo = db.Column(db.Boolean, default=True, nullable=False)


    def __init__(
        self, nome_projeto, data_inicio, responsavel_tecnico_id,
        andamento_id, data_fim=None, observacoes=None, ativo=True
    ):
        self.nome_projeto = nome_projeto
        self.data_inicio = data_inicio
        self.data_fim = data_fim
        self.responsavel_tecnico_id = responsavel_tecnico_id
        self.observacoes = observacoes
        self.andamento_id = andamento_id
        self.ativo = ativo


    @staticmethod
    def listar_projetos():
        return ProjetoModel.query.filter(
            ProjetoModel.deletado == False
        ).order_by(ProjetoModel.id.desc()).all()
    
    
    @staticmethod
    def listar_projetos_ativos():
        return ProjetoModel.query.filter(
            ProjetoModel.ativo == True,
            ProjetoModel.deletado == False
        ).order_by(ProjetoModel.id.desc()).all()
        
        
    @staticmethod
    def obter_projetos_asc_nome():
        return ProjetoModel.query.filter(
            ProjetoModel.deletado == False,
            ProjetoModel.ativo == True
        ).order_by(ProjetoModel.nome_projeto.asc()).all()


    @staticmethod
    def obter_projeto_por_id(id):
        return ProjetoModel.query.filter(
            ProjetoModel.id == id,
            ProjetoModel.deletado == False
        ).first()


    @staticmethod
    def filtrar_projetos(
        nome_projeto=None,
        responsavel_tecnico=None,
        andamento_id=None
    ):
        query = ProjetoModel.query.join(ProjetoModel.responsavel_tecnico).filter(
            ProjetoModel.deletado == False,
            ProjetoModel.ativo == True
        )

        if nome_projeto:
            query = query.filter(
                ProjetoModel.nome_projeto.ilike(f"%{nome_projeto}%")
            )

        if responsavel_tecnico:
            from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
            query = query.filter(
                UsuarioModel.nome.ilike(f"%{responsavel_tecnico}%")
            )

        if andamento_id:
            query = query.filter(ProjetoModel.andamento_id == andamento_id)

        return query.order_by(ProjetoModel.id.desc()).all()


    def adicionar_usuario_envolvido(self, usuario_id):
        """Adiciona um usuário à lista de envolvidos no projeto"""
        from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
        
        usuario = UsuarioModel.query.get(usuario_id)
        if usuario and usuario not in self.usuarios_envolvidos:
            self.usuarios_envolvidos.append(usuario)
            return True
        return False


    def remover_usuario_envolvido(self, usuario_id):
        """Remove um usuário da lista de envolvidos no projeto"""
        from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
        
        usuario = UsuarioModel.query.get(usuario_id)
        if usuario and usuario in self.usuarios_envolvidos:
            self.usuarios_envolvidos.remove(usuario)
            return True
        return False

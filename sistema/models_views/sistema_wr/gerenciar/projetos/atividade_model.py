from sistema.models_views.base_model import BaseModel, db
from datetime import datetime


class AtividadeModel(BaseModel):
    """
    Model para atividades dos projetos
    """
    __tablename__ = 'proj_atividade'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('proj_projeto.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text(length=4294967295), nullable=True)
    horas_necessarias = db.Column(db.Float, default=0.0)
    horas_utilizadas = db.Column(db.Float, default=0.0)
    data_prazo_conclusao = db.Column(db.Date, nullable=True)
    valor_atividade_100 = db.Column(db.Integer, default=0)  # Valor em centavos
    prioridade_id = db.Column(db.Integer, db.ForeignKey('z_sys_prioridade_atividade.id'), nullable=False)
    situacao_id = db.Column(db.Integer, db.ForeignKey('z_sys_andamento_atividade.id'), nullable=False)
    
    supervisor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    desenvolvedor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario_solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    # Relacionamentos    
    supervisor = db.relationship('UsuarioModel', foreign_keys=[supervisor_id], backref='atividades_supervisionadas')
    desenvolvedor = db.relationship('UsuarioModel', foreign_keys=[desenvolvedor_id], backref='atividades_desenvolvimento')
    usuario_solicitante = db.relationship('UsuarioModel', foreign_keys=[usuario_solicitante_id], backref='atividades_solicitadas')
    projeto = db.relationship('ProjetoModel', backref='proj_atividade')
    prioridade = db.relationship('PrioridadeAtividadeModel', backref='proj_atividade')
    situacao = db.relationship('AndamentoAtividadeModel', backref='proj_atividade')
    anexos = db.relationship('AtividadeAnexoModel', backref='proj_atividade', lazy='dynamic', cascade='all, delete-orphan')


    def __init__(self, projeto_id, titulo, prioridade_id, situacao_id, descricao=None, 
                 supervisor_id=None, desenvolvedor_id=None, usuario_solicitante_id=None,
                 horas_necessarias=0.0, horas_utilizadas=0.0, data_prazo_conclusao=None, valor_atividade_100=0):
        self.projeto_id = projeto_id
        self.titulo = titulo
        self.descricao = descricao
        self.supervisor_id = supervisor_id
        self.desenvolvedor_id = desenvolvedor_id
        self.usuario_solicitante_id = usuario_solicitante_id
        self.horas_necessarias = horas_necessarias
        self.horas_utilizadas = horas_utilizadas
        self.data_prazo_conclusao = data_prazo_conclusao
        self.valor_atividade_100 = valor_atividade_100
        self.prioridade_id = prioridade_id
        self.situacao_id = situacao_id
    
    
    @property
    def percentual_horas(self):
        """Retorna o percentual de horas utilizadas"""
        if self.horas_necessarias > 0:
            return min(100, (self.horas_utilizadas / self.horas_necessarias) * 100)
        return 0
    
    
    @property
    def esta_atrasada(self):
        """Verifica se a atividade está atrasada"""
        if self.data_prazo_conclusao:
            return datetime.now().date() > self.data_prazo_conclusao
        return False


    @staticmethod
    def listar_atividades_por_projeto(projeto_id):
        return AtividadeModel.query.filter(
            AtividadeModel.projeto_id == projeto_id,
            AtividadeModel.deletado == False
        ).order_by(
            AtividadeModel.prioridade_id.desc(),
            AtividadeModel.data_cadastro.desc()
        ).all()
        
        
    @staticmethod
    def obter_atividade_por_id(id):
        return AtividadeModel.query.filter(
            AtividadeModel.id == id,
            AtividadeModel.deletado == False
        ).first()
    
    
    @staticmethod
    def listar_atividades_por_prioridade(projeto_id, prioridade_id):
        return AtividadeModel.query.filter(
            AtividadeModel.projeto_id == projeto_id,
            AtividadeModel.prioridade_id == prioridade_id,
            AtividadeModel.deletado == False
        ).order_by(
            AtividadeModel.data_cadastro.desc()
        ).all()
    
    
    @staticmethod
    def atualizar_prioridade(atividade_id, nova_prioridade_id):
        atividade = AtividadeModel.query.get(atividade_id)
        if atividade:
            atividade.prioridade_id = nova_prioridade_id
            db.session.commit()
            return True
        return False


class AtividadeAnexoModel(BaseModel):
    """
    Model para anexos das atividades
    """
    __tablename__ = 'proj_atividade_anexos'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    atividade_id = db.Column(db.Integer, db.ForeignKey('proj_atividade.id'), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)  # imagem, documento, video, etc
    tamanho = db.Column(db.Integer, nullable=False)  # em bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    
    def __init__(self, atividade_id, nome_arquivo, nome_original, caminho_arquivo, 
                 tipo_arquivo, tamanho, mime_type=None):
        self.atividade_id = atividade_id
        self.nome_arquivo = nome_arquivo
        self.nome_original = nome_original
        self.caminho_arquivo = caminho_arquivo
        self.tipo_arquivo = tipo_arquivo
        self.tamanho = tamanho
        self.mime_type = mime_type
    
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho formatado do arquivo"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamanho < 1024.0:
                return f"{self.tamanho:.2f} {unit}"
            self.tamanho /= 1024.0
        return f"{self.tamanho:.2f} TB"
    
    
    @property
    def is_image(self):
        """Verifica se o anexo é uma imagem"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        return any(self.nome_arquivo.lower().endswith(ext) for ext in image_extensions)
    
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho formatado do arquivo"""
        tamanho = self.tamanho
        for unit in ['B', 'KB', 'MB', 'GB']:
            if tamanho < 1024.0:
                return f"{tamanho:.1f} {unit}"
            tamanho /= 1024.0
        return f"{tamanho:.1f} TB"
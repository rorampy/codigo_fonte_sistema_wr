from ....base_model import BaseModel, db


class CategoriaModel(BaseModel):
    """
    Model para categorias de solicitações de atividades.
    Permite classificar solicitações (ex: Bug, Nova Funcionalidade, etc.)
    """
    __tablename__ = 'categorias'

    # Cores permitidas - classes Tabler (mesmas do sistema de tags para consistência)
    CORES_PERMITIDAS = [
        'text-blue', 'text-azure', 'text-indigo', 'text-purple',
        'text-pink', 'text-red', 'text-orange', 'text-yellow',
        'text-lime', 'text-green', 'text-teal', 'text-cyan'
    ]

    # Colunas
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    cor = db.Column(db.String(20), nullable=False)

    def __init__(self, nome, cor, descricao=None):
        """
        Inicializa uma nova categoria.
        
        Args:
            nome (str): Nome da categoria
            cor (str): Classe Tabler da cor (ex: 'text-blue')
            descricao (str, optional): Descrição da categoria
        """
        self.nome = nome
        self.cor = cor
        self.descricao = descricao
        self.deletado = False

    @staticmethod
    def listar_categorias_ativas():
        """
        Lista todas as categorias ativas (não deletadas), ordenadas por nome.
        
        Returns:
            list[CategoriaModel]: Lista de categorias ativas
        """
        return CategoriaModel.query.filter_by(deletado=False).order_by(CategoriaModel.nome).all()

    @staticmethod
    def validar_nome_unico(nome, categoria_id=None):
        """
        Valida se o nome da categoria é único.
        
        Args:
            nome (str): Nome a validar
            categoria_id (int, optional): ID da categoria sendo editada (ignora na validação)
            
        Returns:
            bool: True se nome é único, False se já existe
        """
        query = CategoriaModel.query.filter_by(nome=nome.strip(), deletado=False)
        if categoria_id:
            query = query.filter(CategoriaModel.id != categoria_id)
        return query.first() is None

    @staticmethod
    def validar_cor(cor):
        """
        Valida se a cor está na lista de cores permitidas.
        
        Args:
            cor (str): Classe Tabler da cor (ex: 'text-blue')
            
        Returns:
            bool: True se válida, False caso contrário
        """
        return cor in CategoriaModel.CORES_PERMITIDAS

    @staticmethod
    def obter_nome_cor(classe_tabler):
        """
        Converte classe Tabler em nome legível da cor.
        
        Args:
            classe_tabler (str): Classe Tabler (ex: 'text-blue')
            
        Returns:
            str: Nome da cor (ex: 'Azul')
        """
        nomes = {
            'text-blue': 'Azul',
            'text-azure': 'Azure',
            'text-indigo': 'Índigo',
            'text-purple': 'Roxo',
            'text-pink': 'Rosa',
            'text-red': 'Vermelho',
            'text-orange': 'Laranja',
            'text-yellow': 'Amarelo',
            'text-lime': 'Lima',
            'text-green': 'Verde',
            'text-teal': 'Turquesa',
            'text-cyan': 'Ciano'
        }
        return nomes.get(classe_tabler, classe_tabler)

    @staticmethod
    def obter_categoria_por_id(categoria_id):
        """
        Busca uma categoria pelo ID.
        
        Args:
            categoria_id (int): ID da categoria
            
        Returns:
            CategoriaModel ou None: Categoria encontrada ou None
        """
        return CategoriaModel.query.filter_by(id=categoria_id, deletado=False).first()

    @staticmethod
    def contar_solicitacoes_vinculadas(categoria_id):
        """
        Conta quantas solicitações estão vinculadas a esta categoria.
        
        Args:
            categoria_id (int): ID da categoria
            
        Returns:
            int: Número de solicitações vinculadas
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
        
        return SolicitacaoAtividadeModel.query.filter_by(
            categoria_id=categoria_id,
            deletado=False
        ).count()

    @staticmethod
    def contar_atividades_vinculadas(categoria_id):
        """
        Conta quantas atividades estão vinculadas a esta categoria.
        
        Args:
            categoria_id (int): ID da categoria
            
        Returns:
            int: Número de atividades vinculadas
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
        
        return AtividadeModel.query.filter_by(
            categoria_id=categoria_id,
            deletado=False
        ).count()

    def __repr__(self):
        return f'<Categoria {self.nome}>'
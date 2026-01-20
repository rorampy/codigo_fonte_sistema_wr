from ....base_model import BaseModel, db


class AreaModel(BaseModel):
    """
    Model para areas de solicitações de atividades.
    Permite classificar solicitações (ex: Bug, Nova Funcionalidade, etc.)
    """
    __tablename__ = 'atividade_areas'

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
        Inicializa uma nova area.
        
        Args:
            nome (str): Nome da area
            cor (str): Classe Tabler da cor (ex: 'text-blue')
            descricao (str, optional): Descrição da area
        """
        self.nome = nome
        self.cor = cor
        self.descricao = descricao
        self.deletado = False

    
    def listar_areas_ativas():
        """
        Lista todas as areas ativas (não deletadas), ordenadas por nome.
        
        Returns:
            list[AreaModel]: Lista de areas ativas
        """
        return AreaModel.query.filter_by(deletado=False).order_by(AreaModel.nome).all()

    
    def validar_nome_unico(nome, area_id=None):
        """
        Valida se o nome da area é único.
        
        Args:
            nome (str): Nome a validar
            area_id (int, optional): ID da area sendo editada (ignora na validação)
            
        Returns:
            bool: True se nome é único, False se já existe
        """
        query = AreaModel.query.filter_by(nome=nome.strip(), deletado=False)
        if area_id:
            query = query.filter(AreaModel.id != area_id)
        return query.first() is None

    
    def validar_cor(cor):
        """
        Valida se a cor está na lista de cores permitidas.
        
        Args:
            cor (str): Classe Tabler da cor (ex: 'text-blue')
            
        Returns:
            bool: True se válida, False caso contrário
        """
        return cor in AreaModel.CORES_PERMITIDAS

    
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

    
    def obter_area_por_id(area_id):
        """
        Busca uma area pelo ID.
        
        Args:
            area_id (int): ID da area
            
        Returns:
            AreaModel ou None: area encontrada ou None
        """
        return AreaModel.query.filter_by(id=area_id, deletado=False).first()

    
    def contar_solicitacoes_vinculadas(area_id):
        """
        Conta quantas solicitações estão vinculadas a esta area.
        
        Args:
            area_id (int): ID da area
            
        Returns:
            int: Número de solicitações vinculadas
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
        
        return SolicitacaoAtividadeModel.query.filter_by(
            area_id=area_id,
            deletado=False
        ).count()

    
    def contar_atividades_vinculadas(area_id):
        """
        Conta quantas atividades estão vinculadas a esta area.
        
        Args:
            area_id (int): ID da area
            
        Returns:
            int: Número de atividades vinculadas
        """
        from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
        
        return AtividadeModel.query.filter_by(
            area_id=area_id,
            deletado=False
        ).count()

    def __repr__(self):
        return f'<area {self.nome}>'
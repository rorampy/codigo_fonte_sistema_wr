from ....base_model import BaseModel, db
from sqlalchemy import and_




class TagModel(BaseModel):
    __tablename__ = 'tags'

    CORES_PERMITIDAS = [
        'text-blue', 'text-azure', 'text-indigo', 'text-purple',
        'text-pink', 'text-red', 'text-orange', 'text-yellow',
        'text-lime', 'text-green', 'text-teal', 'text-cyan'
    ]

    # Chave Primária
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Dados da tag
    nome = db.Column(db.String(100), nullable=False)
    cor = db.Column(db.String(20), nullable=False)  # Armazena a classe CSS
    descricao = db.Column(db.String(255), nullable=True)  # Descrição opcional da tag
    

    #Exclusão Lógica
    deletado = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, nome, cor, descricao=None):
        """
        Construtor da classe TagModel

        Args:
            nome (str): Nome da tag
            cor (str): Cor da tag em formato hexadecimal
            descricao (str): Descrição opcional da tag
        """
        self.nome = nome
        self.cor = cor
        self.descricao = descricao
        self.deletado = False

    @staticmethod
    def listar_tags_ativas():
        """
        Retorna todas as tags ativas (não deletadas), ordenadas por nome.
        
        Returns:
            list[TagModel]: Lista de tags ativas
        """
        return TagModel.query.filter_by(deletado=False).order_by(TagModel.nome).all()
    
    @staticmethod
    def validar_nome_unico(nome, tag_id=None):
        """
        Valida se o nome da tag é único (exceto se for edição da mesma tag).
        
        Args:
            nome (str): Nome da tag a validar
            tag_id (int, optional): ID da tag sendo editada (ignora ela na validação)
            
        Returns:
            bool: True se nome é único/válido, False se já existe
        """
        query = TagModel.query.filter_by(nome=nome.strip(), deletado=False)
        if tag_id:
            query = query.filter(TagModel.id != tag_id)
        return query.first() is None
    
    @staticmethod
    def validar_cor(cor):
        """
        Valida se a cor fornecida está na lista de cores permitidas.
        
        Args:
            cor (str): Cor a validar
            
        Returns:
            bool: True se a cor é válida, False caso contrário
        """
        return cor in TagModel.CORES_PERMITIDAS
    
    @staticmethod
    def obter_nome_cor(classe_css):
        """
        Retorna o nome legível da cor a partir da classe CSS.
        
        Args:
            classe_css (str): Classe CSS (ex: text-blue)
            
        Returns:
            str: Nome da cor (ex: Azul)
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
        return nomes.get(classe_css, classe_css)
    
    @staticmethod
    def obter_tag_por_id(tag_id):
        """
        Obtém uma tag pelo seu ID.
        
        Args:
            tag_id (int): ID da tag
            
        Returns:
            TagModel ou None: Instância da tag ou None se não encontrada
        """
        return TagModel.query.filter_by(id=tag_id, deletado=False).first()

    def __repr__(self):
        return f'<Tag {self.nome}>'
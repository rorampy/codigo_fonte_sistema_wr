from .....base_model import BaseModel, db
from sqlalchemy.orm import relationship


class CategoriaLancamentoModel(BaseModel):
    """
    Model para registro de plano de conta
    """
    
    __tablename__ = "ca_categoria_lancamento"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Integer, nullable=False)  # 1=Receita, 2=Despesa, 3=Movimentação
    nivel = db.Column(db.Integer, nullable=False, default=1)  # 1=Principal, 2=Sub, 3=SubSub
    parent_id = db.Column(db.Integer, db.ForeignKey('ca_categoria_lancamento.id'), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamentos
    parent = relationship("CategoriaLancamentoModel", remote_side=[id], backref="children")
    
    def __init__(self, codigo=None, nome=None, tipo=None, parent_id=None, nivel=1, ativo=True):
        self.codigo = codigo
        self.nome = nome
        self.tipo = tipo
        self.parent_id = parent_id
        self.nivel = nivel
        self.ativo = ativo
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """Busca categoria por código (apenas ativas)"""
        return cls.query.filter_by(codigo=codigo, ativo=True).first()
    
    @classmethod
    def buscar_principais(cls):
        """Busca categorias principais (nível 1, apenas ativas)"""
        return cls.query.filter_by(nivel=1, ativo=True).order_by(cls.codigo).all()
    
    @classmethod
    def buscar_filhos(cls, parent_id):
        """Busca subcategorias de uma categoria pai (apenas ativas)"""
        return cls.query.filter_by(parent_id=parent_id, ativo=True).order_by(cls.codigo).all()
    
    @classmethod
    def gerar_proximo_codigo(cls, parent_code=None):
        """Gera o próximo código disponível"""
        if parent_code is None:
            return None
        
        if '.' not in parent_code:
            # Para subcategorias (1.01, 1.02, etc.)
            subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                ~cls.codigo.like(f"{parent_code}.%.%"),
                cls.ativo == True 
            ).all()
            
            if not subcategorias:
                return f"{parent_code}.01"
            
            # Extrair números das subcategorias ativas
            numeros = []
            for sub in subcategorias:
                try:
                    num = int(sub.codigo.split('.')[1])
                    numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            # Encontrar próximo número disponível
            proximo = 1
            while proximo in numeros:
                proximo += 1
            
            return f"{parent_code}.{proximo:02d}"
        
        else:
            sub_subcategorias = cls.query.filter(
                cls.codigo.like(f"{parent_code}.%"),
                cls.ativo == True  
            ).all()
            
            if not sub_subcategorias:
                return f"{parent_code}.01"
            
            # Extrair números das sub-subcategorias ativas
            numeros = []
            for subsub in sub_subcategorias:
                try:
                    parts = subsub.codigo.split('.')
                    if len(parts) == 3:
                        num = int(parts[2])
                        numeros.append(num)
                except (IndexError, ValueError):
                    continue
            
            # Encontrar próximo número disponível
            proximo = 1
            while proximo in numeros:
                proximo += 1
            
            return f"{parent_code}.{proximo:02d}"
    
    @classmethod
    def verificar_codigo_disponivel(cls, codigo):
        """Verifica se um código está disponível (não existe ou não está ativo)"""
        existe_ativo = cls.query.filter_by(codigo=codigo, ativo=True).first()
        return existe_ativo is None
    
    @classmethod
    def reativar_categoria(cls, codigo):
        """Reativa uma categoria que foi excluída (soft delete)"""
        categoria_inativa = cls.query.filter_by(codigo=codigo, ativo=False).first()
        if categoria_inativa:
            categoria_inativa.ativo = True
            db.session.commit()
            return categoria_inativa
        return None
    
    def calcular_nivel(self):
        """Calcula o nível baseado no código"""
        if '.' not in self.codigo:
            return 1
        elif self.codigo.count('.') == 1:
            return 2
        else:
            return 3
    
    def get_children_ordenados(self):
        """Retorna filhos ordenados por código (apenas ativos)"""
        return self.__class__.query.filter_by(
            parent_id=self.id,
            ativo=True  
        ).order_by(self.__class__.codigo).all()
    
    def soft_delete(self):
        """Exclui categoria (soft delete) e todos os filhos"""
        # Excluir filhos recursivamente
        filhos = self.get_children_ordenados()
        for filho in filhos:
            filho.soft_delete()
        
        # Excluir esta categoria
        self.ativo = False
        db.session.commit()
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'tipo': self.tipo,
            'nivel': self.nivel,
            'parent_id': self.parent_id,
            'ativo': self.ativo
        }


def criar_categoria_com_tratamento_duplicacao(codigo, nome, tipo, parent_id=None, nivel=1):
    """
    Cria categoria com tratamento inteligente de duplicação
    """
    try:
        # Verificar se código já existe como registro ativo
        categoria_existente = CategoriaLancamentoModel.buscar_por_codigo(codigo)
        if categoria_existente:
            raise ValueError(f"Código {codigo} já existe e está ativo")
        
        # Verificar se existe registro inativo com mesmo código
        categoria_inativa = CategoriaLancamentoModel.query.filter_by(codigo=codigo, ativo=False).first()
        
        if categoria_inativa:
            # Reativar categoria existente
            categoria_inativa.nome = nome  # Atualizar nome
            categoria_inativa.ativo = True
            db.session.commit()
            return categoria_inativa
        else:
            # Criar nova categoria
            nova_categoria = CategoriaLancamentoModel(
                codigo=codigo,
                nome=nome,
                tipo=tipo,
                parent_id=parent_id,
                nivel=nivel
            )
            db.session.add(nova_categoria)
            db.session.commit()
            return nova_categoria
            
    except Exception as e:
        db.session.rollback()
        raise
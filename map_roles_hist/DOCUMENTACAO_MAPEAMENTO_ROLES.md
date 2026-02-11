# Documentação — Mapeamento de Roles (Painel Administrativo)

Guia completo para portar a funcionalidade de **Gerenciamento de Mapeamento de Roles via interface web** para outro sistema Flask com estrutura semelhante.

---

## 1. Visão Geral

Esta funcionalidade permite que o administrador (role `root`) gerencie **em tempo real**, pela interface web, quais roles têm acesso a cada rota do sistema. As alterações refletem imediatamente (sem necessidade de reiniciar o servidor) e possuem auditoria completa com possibilidade de reversão.

### Funcionalidades
- **CRUD completo** de mapeamentos rota → roles
- **Descrições** opcionais por rota
- **Histórico/Auditoria** com linha do tempo, busca e filtros
- **Reversão** de qualquer alteração (dupla confirmação)
- **Atualização em memória** do dict de permissões (efeito imediato)
- **KPIs** de resumo (total de rotas, roles, alterações)

---

## 2. Pré-requisitos do Sistema Destino

O sistema destino deve possuir:

| Requisito | Descrição |
|-----------|-----------|
| **Flask** | Framework web |
| **Flask-Login** | Autenticação (`@login_required`, `current_user`) |
| **SQLAlchemy** | ORM com model de roles (ou equivalente) |
| **Bootstrap/Tabler** | Framework CSS para os modais e tabela |
| **Jinja2** | Template engine (padrão do Flask) |
| **Arquivo `mapeamento_roles.py`** | Dict Python com o mapeamento rota → roles |
| **Decorator `@requires_roles`** | Que lê do dict `mapeamento_roles` para controlar acesso |
| **Logger** (opcional) | Para registrar ações (`flask_logger` ou similar) |

---

## 3. Estrutura de Arquivos

```
projeto/
├── mapeamento_roles.py                      # Dict de permissões (já existente)
├── map_roles_hist/                           # CRIAR — pasta de histórico
│   ├── map_roles_hist.json                   # CRIAR — histórico de alterações (iniciar com [])
│   ├── map_roles_desc.json                   # CRIAR — descrições de rotas (iniciar com {})
│   └── DOCUMENTACAO_MAPEAMENTO_ROLES.md      # Esta documentação
├── sistema/
│   ├── __init__.py                           # EDITAR — registrar import da view
│   ├── models_views/.../mapeamento_roles/
│   │   ├── __init__.py                       # CRIAR — vazio
│   │   └── mapeamento_roles_view.py          # CRIAR — toda a lógica (rotas + helpers)
│   └── templates/.../mapeamento_roles/
│       └── mapeamento_roles_listar.html      # CRIAR — template completo
```

---

## 4. Passo a Passo de Implementação

### 4.1. Criar a pasta de histórico

```bash
mkdir -p map_roles_hist
echo "[]" > map_roles_hist/map_roles_hist.json
echo "{}" > map_roles_hist/map_roles_desc.json
```

### 4.2. Verificar o `mapeamento_roles.py`

O arquivo deve ter exatamente este formato:

```python
# Defina todos os mapeamentos aqui
mapeamento_roles = {
    'nome_da_rota': ['role1', 'role2'],
    'outra_rota': ['role1'],
}
```

> **Importante:** A view reescreve este arquivo inteiro ao salvar. Não coloque imports, comentários extras ou lógica nele.

### 4.3. Verificar o decorator `@requires_roles`

No `__init__.py` do seu app Flask, o decorator deve:
1. Importar o dict: `from mapeamento_roles import mapeamento_roles`
2. Ler a role do usuário: `current_user.role.nome`
3. Verificar se a role está na lista da rota

Exemplo:

```python
from mapeamento_roles import mapeamento_roles

def requires_roles(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        endpoint = request.endpoint
        required_roles = mapeamento_roles.get(endpoint, [])
        user_role = current_user.role.nome
        if user_role not in required_roles:
            return render_template('paginas_erro/erro_401.html')
        return f(*args, **kwargs)
    return wrapped
```

### 4.4. Verificar o model de Role

Você precisa de um model com método estático que retorne todas as roles ativas:

```python
class RoleModel(BaseModel):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)

    def obter_roles_desc_id():
        return RoleModel.query.filter(
            RoleModel.deletado == 0
        ).order_by(desc(RoleModel.id)).all()
```

> **Adapte** o nome da classe, tabela e campo de exclusão lógica (`deletado`) conforme seu projeto.

### 4.5. Criar a View (`mapeamento_roles_view.py`)

Copie o arquivo `mapeamento_roles_view.py` e ajuste os seguintes pontos:

#### Caminhos dos arquivos (linhas 13-25)

Os caminhos usam `..` relativos. Conte quantos níveis de pasta separam a view da raiz do projeto:

```python
# Exemplo original (6 níveis acima):
MAPEAMENTO_ROLES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', '..', '..', '..', '..', 'mapeamento_roles.py'
)
```

**Adapte** a quantidade de `..` para corresponder à sua estrutura. Alternativamente, use o caminho absoluto:

```python
import pathlib
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[6]  # ajuste o número
MAPEAMENTO_ROLES_PATH = str(PROJECT_ROOT / 'mapeamento_roles.py')
HISTORICO_PATH = str(PROJECT_ROOT / 'map_roles_hist' / 'map_roles_hist.json')
DESCRICOES_PATH = str(PROJECT_ROOT / 'map_roles_hist' / 'map_roles_desc.json')
```

#### Imports (linhas 1-10)

```python
import os
import json
from datetime import datetime

import mapeamento_roles as _mr_modulo          # para atualizar dict em memória
from sistema import app, requires_roles        # ADAPTE ao seu app
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from logs_sistema import flask_logger           # ADAPTE ao seu logger
from sistema.models_views...role_model import RoleModel  # ADAPTE ao seu model
```

#### Atualização em memória (dentro de `_salvar_mapeamento`)

A linha crítica que garante efeito imediato:

```python
import mapeamento_roles as _mr_modulo

def _salvar_mapeamento(mapeamento):
    # ... (salva arquivo) ...
    
    # Atualiza dict em memória — essencial!
    _mr_modulo.mapeamento_roles.clear()
    _mr_modulo.mapeamento_roles.update(mapeamento)
```

> Isso funciona porque `from mapeamento_roles import mapeamento_roles` no `__init__.py` cria uma referência ao **mesmo objeto dict**. Mutações via `.clear()` + `.update()` são visíveis em todos os módulos que apontam para esse dict.

#### Nome do usuário no histórico (dentro de `_registrar_historico`)

```python
'usuario': f'{current_user.nome} {current_user.sobrenome}',
```

**Adapte** para os campos do seu model de usuário. Exemplos:
- `current_user.name`
- `current_user.username`
- `f'{current_user.first_name} {current_user.last_name}'`

### 4.6. Criar o Template

Copie `mapeamento_roles_listar.html` e ajuste:

| O que ajustar | Onde | Como |
|---------------|------|------|
| Template base | Linha 1 | `{% extends 'sua_base.html' %}` |
| Header/sidebar | Linha 3 | `{% include 'seu_header.html' %}` |
| Footer | Fim do arquivo | `{% include 'seu_footer.html' %}` |
| Flash messages | Dentro do body | `{% include 'sua_mensagem_flash.html' %}` |
| Block name | Linha 2 | `{% block conteudo %}` → adapte ao nome do seu block |
| CSS framework | Classes CSS | Se não usa Tabler, adapte `.card`, `.badge`, `.btn`, `.modal` etc. |

### 4.7. Registrar a View no App

No final do `__init__.py` do seu app, adicione o import:

```python
# Configurações - Mapeamento de Roles
from sistema.models_views...mapeamento_roles import mapeamento_roles_view
```

> Sem este import, as rotas **não serão registradas**.

### 4.8. Registrar as Roles no `mapeamento_roles.py`

Adicione as 5 rotas novas ao seu `mapeamento_roles.py`:

```python
'map_roles_listar': ['root'],
'map_roles_adicionar': ['root'],
'map_roles_editar': ['root'],
'map_roles_excluir': ['root'],
'map_roles_reverter': ['root'],
```

> **Recomendação:** restrinja ao role mais alto (`root`/`admin`). Esta é uma funcionalidade de super-administrador.

### 4.9. Adicionar link no menu/sidebar (opcional)

No seu template de navegação, adicione um link:

```html
<a class="nav-link" href="{{ url_for('map_roles_listar') }}">
    Mapeamento de Roles
</a>
```

---

## 5. Rotas Criadas

| Método | URL | Endpoint | Ação |
|--------|-----|----------|------|
| GET | `/configuracoes/mapeamento-roles` | `map_roles_listar` | Lista todos os mapeamentos |
| POST | `/configuracoes/mapeamento-roles/adicionar` | `map_roles_adicionar` | Adiciona nova rota |
| POST | `/configuracoes/mapeamento-roles/editar` | `map_roles_editar` | Edita rota existente |
| POST | `/configuracoes/mapeamento-roles/excluir` | `map_roles_excluir` | Remove rota |
| POST | `/configuracoes/mapeamento-roles/reverter` | `map_roles_reverter` | Reverte alteração pelo histórico |

> URLs são customizáveis. Altere nos decorators `@app.route(...)` na view.

---

## 6. Arquitetura dos Dados

### `mapeamento_roles.py`
```python
mapeamento_roles = {
    'endpoint_flask': ['role1', 'role2'],
}
```

### `map_roles_hist.json` (array de entradas)
```json
[
  {
    "id": "20260211112735103669",
    "usuario": "Nome Sobrenome",
    "usuario_id": 10,
    "acao": "adicionou|editou|removeu|reverteu",
    "chave": "nome_da_rota",
    "conteudo": "Descrição legível da alteração",
    "data_hora": "11/02/2026 11:27:35",
    "revertido": false,
    "justificativa": "Motivo opcional",
    "chave_anterior": "nome_antigo (se renomeou)",
    "estado_anterior": ["role1", "role2"],
    "estado_novo": ["role1", "role3"],
    "revertido_por": "Nome (se revertido)",
    "revertido_em": "dd/mm/aaaa hh:mm:ss (se revertido)"
  }
]
```

### `map_roles_desc.json`
```json
{
  "nome_da_rota": "Descrição amigável da rota"
}
```

---

## 7. Fluxo de Funcionamento

```
Usuário root abre /configuracoes/mapeamento-roles
         │
         ├─ _ler_mapeamento()  → lê mapeamento_roles.py via exec()
         ├─ _ler_historico()   → lê map_roles_hist.json
         ├─ _ler_descricoes()  → lê map_roles_desc.json
         └─ RoleModel.obter_roles_desc_id() → roles do banco
         │
         ▼
    Renderiza template com mapeamento + histórico + roles
         │
         ├─ [Adicionar] → POST → valida → _salvar_mapeamento() → _registrar_historico()
         ├─ [Editar]    → POST → valida → _salvar_mapeamento() → _registrar_historico()
         ├─ [Excluir]   → POST → valida → _salvar_mapeamento() → _registrar_historico()
         └─ [Reverter]  → POST → valida conflitos → _salvar_mapeamento() → marca revertido
                                                                           → _registrar_historico()
         │
         ▼
    _salvar_mapeamento() também faz:
         _mr_modulo.mapeamento_roles.clear()
         _mr_modulo.mapeamento_roles.update(novo)
         → Efeito IMEDIATO no @requires_roles
```

---

## 8. Checklist de Testes Manuais

Após portar, valide cada item:

- [ ] **Listar:** Página carrega com todas as rotas, badges de roles, KPIs corretos
- [ ] **Pesquisa:** Digitar parte do nome da rota filtra a tabela em tempo real
- [ ] **Adicionar:** Criar rota nova → aparece na tabela → funciona no `@requires_roles` imediatamente
- [ ] **Adicionar duplicada:** Tentar adicionar rota que já existe → flash de aviso
- [ ] **Editar roles:** Mudar roles de uma rota → badges atualizam → acesso muda imediatamente
- [ ] **Editar nome:** Renomear rota → nome antigo some, novo aparece
- [ ] **Editar com justificativa:** Preencher justificativa → aparece no histórico
- [ ] **Excluir:** Remover rota → some da tabela → acesso bloqueado imediatamente
- [ ] **Histórico:** Abrir modal → todas as ações aparecem com cores corretas
- [ ] **Histórico busca:** Buscar por nome de rota ou usuário → filtra corretamente
- [ ] **Histórico filtros:** Clicar em "Adições", "Edições", etc. → filtra por tipo
- [ ] **Reverter adição:** Reverter uma adição → rota é removida
- [ ] **Reverter remoção:** Reverter uma remoção → rota é restaurada com roles originais
- [ ] **Reverter edição:** Reverter uma edição → roles voltam ao estado anterior
- [ ] **Reverter com conflito:** Tentar reverter remoção de rota que já existe → flash de aviso
- [ ] **Dupla confirmação:** Clicar "Reverter" → modal de confirmação aparece → cancelar volta ao histórico
- [ ] **Sem reiniciar:** Todas as alterações refletem imediatamente no controle de acesso

---

## 9. Possíveis Adaptações

### Se o sistema usa Blueprints (ao invés de `@app.route`)
Troque `from sistema import app` por:

```python
from flask import Blueprint
mapeamento_bp = Blueprint('mapeamento', __name__)

@mapeamento_bp.route('/configuracoes/mapeamento-roles')
# ...
```

E registre no app: `app.register_blueprint(mapeamento_bp)`

### Se o sistema tem múltiplas roles por usuário (N:N)
No `requires_roles`, troque:
```python
# De (1:1):
user_role = current_user.role.nome
if user_role not in required_roles:

# Para (N:N):
user_roles = [role.nome for role in current_user.roles]
if not any(role in user_roles for role in required_roles):
```

### Se não usa exclusão lógica (`deletado`)
No method `obter_roles_desc_id()`, remova o filtro:
```python
def obter_roles_desc_id():
    return RoleModel.query.order_by(desc(RoleModel.id)).all()
```

### Se quer limitar o histórico
O sistema já limita a 100 registros na listagem (`historico[:100]`). Para limitar o arquivo JSON, adicione trecho em `_salvar_historico`:

```python
def _salvar_historico(historico):
    # Manter apenas os últimos 500 registros
    historico = historico[:500]
    with open(HISTORICO_PATH, 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)
```

---

## 10. Observações de Segurança

1. **Restrinja ao role mais alto** — Esta funcionalidade altera permissões globais do sistema.
2. **`exec()` é usado** para ler o `mapeamento_roles.py` — Seguro neste contexto pois o arquivo é controlado internamente e somente editado pela própria view.
3. **Sem CSRF explícito** — Se seu projeto usa `Flask-WTF` com proteção CSRF global, os forms POST já estarão protegidos. Caso contrário, considere adicionar `{{ csrf_token() }}` nos forms.
4. **Escrita em arquivo** — Não é atômica. Em ambientes com múltiplos workers, considere usar `fcntl.flock()` ou migrar para banco de dados.

---

## 11. Resumo das Dependências

```
Flask, Flask-Login, Flask-SQLAlchemy (para o model de Role)
Bootstrap 5 ou Tabler (para os componentes de UI)
Nenhuma dependência externa adicional (usa json, os, datetime da stdlib)
```

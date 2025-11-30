import os
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, abort, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from mapeamento_roles import mapeamento_roles
from datetime import datetime, timedelta
from functools import wraps
from config import *


app = Flask(__name__)
app.config['SECRET_KEY'] = CHAVE_SECRETA_FLASK
app.config['SESSION_TYPE'] = 'filesystem' # para utilizar sessão
app.config.from_object('config')


# instância banco
db = SQLAlchemy()
db.init_app(app)

# instância migration
mi = Migrate(app, db)

# login
login_manager = LoginManager(app)

@login_manager.unauthorized_handler
def unauthorized():
    # Verifica se a rota de origem e uma rota protegida diferente de login
    if request.endpoint != 'login':
        flash((f'Você precisa estar logado para acessar esta página!', 'warning'))
    return redirect(url_for('login'))


def requires_roles(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Obtendo nome da rota automaticamente
        endpoint = request.endpoint
        required_roles = mapeamento_roles.get(endpoint, [])
        
        # se for em um relacionamento N-N entre usuario e roles
        #user_roles = [role.nome for role in current_user.roles]
        user_role = current_user.role.nome
        
        #if not any(role in user_roles for role in required_roles):
        if not user_role in required_roles:
            return render_template('sistema_wr/paginas_erro/erro_401.html')
            
        return f(*args, **kwargs)
    return wrapped


# uploads
app.config['UPLOADED_USERS'] = UPLOAD_USERS
app.config['UPLOADED_ANEXOS_SOLICITACOES'] = UPLOAD_ANEXOS_SOLICITACOES
app.config['UPLOADED_ANEXOS_ATIVIDADES'] = UPLOAD_ANEXOS_ATIVIDADES
app.config['UPLOAD_COMPROVANTE_LANCAMENTO_SAIDA'] = UPLOAD_COMPROVANTE_LANCAMENTO_SAIDA
app.config['UPLOAD_CONTRATO_ASSINADO'] = UPLOAD_CONTRATO_ASSINADO
app.config['UPLOAD_COMPROVANTE_RECEBIMENTO'] = UPLOAD_COMPROVANTE_RECEBIMENTO

# tornando a pasta 'uploads' acessível no front
# determinar o caminho para a pasta raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


@app.route('/uploads/_info_users/<filename>')
def diretorio_uploads_usuarios(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_info_users', filename)
    if not os.path.isfile(caminho_arquivo):
        imagem_padrao = 'usuario_sem_foto.png'
        return send_from_directory(
            os.path.join(PROJECT_ROOT, '..', 'uploads/_info_users'), 
            imagem_padrao
        )
        
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_info_users'), 
        filename
    )


@app.route('/uploads/_anexos_atividades/<filename>')
def diretorio_uploads_anexos_atividades(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_anexos_atividades', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_anexos_atividades'), 
        filename
    )

@app.route('/uploads/_comprovante_lancamento_saida/<filename>')
def diretorio_uploads_comprovante_lancamento_saida(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_lancamento_saida', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_lancamento_saida'), 
        filename
    )

@app.route('/uploads/_contrato_assinado/<filename>')
def diretorio_upload_contrato_assinado(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_contrato_assinado', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir
    
    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_contrato_assinado'),
        filename
    )

@app.route('/uploads/_comprovante_recebimento/<filename>')
def diretorio_upload_comprovante_recebimento(filename):
    # Valida se o arquivo existe
    caminho_arquivo = os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_recebimento', filename)
    if not os.path.isfile(caminho_arquivo):
        abort(404)  # Retorna erro 404 se o arquivo não existir

    return send_from_directory(
        os.path.join(PROJECT_ROOT, '..', 'uploads/_comprovante_recebimento'),
        filename
    )

def obter_url_absoluta_de_imagem(nome_imagem):
    # Obtem o caminho absoluto para a pasta 'static'
    static_folder = current_app.static_folder
    # Cria o caminho absoluto para a imagem
    image_path = os.path.join(static_folder, 'images', nome_imagem)
    
    return image_path

# funções para front
# Função para formatar valores em Real Brasileiro (BRL)
def formatar_float_para_brl(valor):
    # Arredonda o valor para duas casas decimais
    valor_formatado = valor / 100

    # Converte o valor formatado para uma string
    valor_str = "{:,.2f}".format(valor_formatado)

    # Substitui ',' por '.' e vice-versa, para atender ao formato BRL
    valor_str = valor_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')

    # Adiciona o símbolo R$
    valor_str = "R$ " + valor_str

    return valor_str

# Função para formatar valores em Dólar Americano (USD)
def formatar_float_para_usd(valor):
    # Arredonda o valor para duas casas decimais
    valor_formatado = valor / 100

    # Converte o valor formatado para uma string
    valor_str = "{:,.2f}".format(valor_formatado)

    # Substitui ',' por '.' para separar os milhares
    valor_str = valor_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')

    # Adiciona o símbolo $
    valor_str = "$ " + valor_str

    return valor_str

# Exibe um objeto datetime no formato de data do Brasil
def formatar_data_para_brl(data):
    # Formata a data para o padrão brasileiro dd/mm/aaaa
    return data.strftime('%d/%m/%Y')

def formatar_data_hora(data_entrada) -> str:
    """
    Aceita datetime ou string no formato 'YYYY-MM-DD HH:MM:SS' e retorna 'DD/MM/YYYY HH:MM:SS'
    """
    if isinstance(data_entrada, str):
        data_obj = datetime.strptime(data_entrada, "%Y-%m-%d %H:%M:%S")
    elif isinstance(data_entrada, datetime):
        data_obj = data_entrada
    else:
        raise ValueError("Tipo de dado inválido para data")

    return data_obj.strftime("%d/%m/%Y %H:%M:%S")

def converte_data_para_datetime_converte_data_brl(data):
    # Converte a string para um objeto datetime
    data_obj = datetime.strptime(data, '%Y-%m-%d')
    
    # Formata a data para o padrão brasileiro dd/mm/aaaa
    return data_obj.strftime('%d/%m/%Y')

# Exibe um objeto datetime no formato de data e hora do Brasil
def formatar_data_hora_para_brl(data):
    # Formata a data para o padrão brasileiro dd/mm/aaaa hh:mm
    return data.strftime('%d/%m/%Y %H:%M')

# Função helper para usar no template
def formatar_tamanho_arquivo(tamanho_bytes):
    """Função standalone para formatar tamanho de arquivos"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.1f} {unit}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.1f} TB"

app.jinja_env.globals['formatar_tamanho'] = formatar_tamanho_arquivo
app.jinja_env.filters['formatar_float_para_brl'] = formatar_float_para_brl
app.jinja_env.filters['formatar_float_para_usd'] = formatar_float_para_usd
app.jinja_env.filters['formatar_data_para_brl'] = formatar_data_para_brl
app.jinja_env.filters['formatar_data_hora_para_brl'] = formatar_data_hora_para_brl
app.jinja_env.filters['formatar_data_hora'] = formatar_data_hora
app.jinja_env.filters['converte_data_para_datetime_converte_data_brl'] = converte_data_para_datetime_converte_data_brl
app.jinja_env.filters['obter_url_absoluta_de_imagem'] = obter_url_absoluta_de_imagem

# models e rotas
from sistema.models_views import base_model
from sistema.models_views.upload_arquivo import upload_arquivo_model
from sistema.models_views.sistema_wr.parametrizacao import changelog_model
from sistema.models_views.sistema_wr.autenticacao import role_model
from sistema.models_views.sistema_wr.parametrizacao import variavel_sistema_model
from sistema.models_views.sistema_wr.autenticacao import usuario_model
from sistema.models_views.sistema_wr.gerenciar.projetos import projeto_andamento_model
from sistema.models_views.sistema_wr.gerenciar.projetos import projeto_model
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_andamento_model
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_prioridade_model
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_model
from sistema.models_views.sistema_wr.gerenciar.projetos import lancamento_horas_model
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_solicitacao_model

# Gerenciar
from sistema.models_views.sistema_wr.gerenciar.clientes import cliente_model
from sistema.models_views.sistema_wr.gerenciar.clientes import cliente_view
from sistema.models_views.sistema_wr.gerenciar.produtos import produto_model
from sistema.models_views.sistema_wr.gerenciar.produtos import produto_view

from sistema.models_views.upload_arquivo import upload_arquivo_view
from sistema.models_views.sistema_wr.parametrizacao import changelog_view
from sistema.models_views.sistema_wr.parametrizacao import variavel_sistema_view
from sistema.models_views.sistema_wr.autenticacao import login_view
from sistema.models_views.sistema_wr.autenticacao import role_view
from sistema.models_views.sistema_wr.autenticacao import usuario_view
from sistema.models_views.sistema_wr.gerenciar.projetos import projeto_andamento_view
from sistema.models_views.sistema_wr.gerenciar.projetos import projeto_view
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_andamento_view
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_prioridade_view
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_view
from sistema.models_views.sistema_wr.gerenciar.projetos import lancamento_horas_view
from sistema.models_views.sistema_wr.gerenciar.projetos import kanban_view
from sistema.models_views.sistema_wr.gerenciar.projetos import atividade_solicitacao_view

# Relatórios
from sistema.models_views.sistema_wr.relatorios.relatorio_horas_dev import relatorio_horas_dev_view


# Financeiro
from sistema.models_views.sistema_wr.financeiro.lancamento import lancamento_model
from sistema.models_views.sistema_wr.financeiro.lancamento import lancamento_view
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira import movimentacao_financeira_model
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira import movimentacao_financeira_view

# Plano de Conte
from sistema.models_views.sistema_wr.configuracoes.gerais.plano_conta import plano_conta_model
from sistema.models_views.sistema_wr.configuracoes.gerais.plano_conta import plano_conta_view

from sistema.models_views.sistema_wr.financeiro.recebimento import status_financeiro_model
from sistema.models_views.sistema_wr.financeiro.recebimento import recebimento_model
from sistema.models_views.sistema_wr.financeiro.recebimento import recebimento_view

# DRE
from sistema.models_views.sistema_wr.financeiro.relatorio_menu.relatorio_menu_view import demonstrativo_de_resultados, dre_pdf

# Contrato
from sistema.models_views.sistema_wr.contrato import contrato_model
from sistema.models_views.sistema_wr.contrato import contrato_view
from sistema.models_views.sistema_wr.contrato import contrato_produto

# Configurações
from sistema.models_views.sistema_wr.configuracoes.gerais.modelo_contrato import modelo_contrato_model
from sistema.models_views.sistema_wr.configuracoes.gerais.modelo_contrato import modelo_contrato_view
from sistema.models_views.sistema_wr.configuracoes.gerais.variaveis_contrato import variavel_modelo_contrato_model

# Variáveis do sistema
from sistema.models_views.sistema_wr.parametrizacao import forma_pagamento_model

# Site Hash
from sistema.models_views.site_wr import site_wr_view
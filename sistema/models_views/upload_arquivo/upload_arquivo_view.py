import os
import random, string
from flask import jsonify
from werkzeug.utils import secure_filename
from sistema import db, app, request
from sistema.models_views.upload_arquivo.upload_arquivo_model import UploadArquivoModel
from sistema._utilitarios import DataHora


def upload_arquivo(arquivo, pasta_destino, nome_referencia=""):
    """
    Função para realizar upload de arquivos no sistema.

    Parâmetros:
    - arquivo: O arquivo recebido do formulário (request.files).
    - pasta_destino: Caminho da pasta onde o arquivo será armazenado. Ex.: 'UPLOADED_USERS'
    - nome_referencia: (Opcional) String adicional para compor o nome do arquivo.

    Retorno:
    - ID do arquivo salvo no banco, ou None se não houver upload.
    """
    if not arquivo or not arquivo.filename:
        return None  # Retorna None se nenhum arquivo foi enviado
    
    if nome_referencia == "":
        nome_referencia = ''.join(random.choices(string.ascii_uppercase, k=6))

    # Gera um nome seguro e único para o arquivo
    nome_arquivo = f'{DataHora.obter_data_atual_padrao_en()}_{nome_referencia}_{arquivo.filename}'
    filename = secure_filename(nome_arquivo)

    # Define o caminho completo onde o arquivo será salvo
    file_path = os.path.join(app.config[f'{pasta_destino}'], filename)

    # Salva o arquivo no caminho especificado
    arquivo.save(file_path)

    # Obtém extensão e tamanho do arquivo
    extensao = os.path.splitext(arquivo.filename)[1]
    tamanho = os.path.getsize(file_path)

    # Salva informações do arquivo no banco de dados
    arquivo_model = UploadArquivoModel(filename, file_path, extensao, tamanho)
    db.session.add(arquivo_model)
    db.session.commit()

    return arquivo_model

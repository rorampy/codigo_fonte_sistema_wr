from flask import make_response
from config import *
import pdfkit
import os
import random


class ManipulacaoArquivos:
    '''
    Classe responsável devolver um arquivo PDF como resposta a uma 
    requisição.
    '''
    
    def gerar_pdf_from_html(html, nome_arquivo):
        '''
        Recebe como parâmetro um template HTML renderizado e um nome para o arquivo
        PDF de saída.
        '''
        options = {
            'enable-local-file-access': '',     # habilita acesso a arquivos locais
            'encoding': 'UTF-8' 
        }

        # Gerar o PDF a partir do HTML
        arquivo_pdf = pdfkit.from_string(html, False, configuration=pdfkit_config, options=options)

        # Retorna o PDF como resposta da requisição
        resposta = make_response(arquivo_pdf)
        resposta.headers['Content-Type'] = 'application/pdf'
        resposta.headers['Content-Disposition'] = f'attachment; filename={nome_arquivo}.pdf'

        return resposta
        
        

    def mover_e_renomear_arquivo(caminho_atual, novo_caminho, novo_nome=None):
        '''
        Recebe como parâmetro o 'caminho atual' do arquivo (diretorio/nome.extensao),
        o 'novo caminho' (diretório/) e o 'novo nome' para arquivo (novo_nome_arquivo.extensao).
        A função verifica se o 'caminho_atual' e o 'novo caminho' existem e se o 'nome do arquivo'
        foi enviado. Caso sim, move e renomeia o arquivo e retorna um dicionário com a chave
        'validado' e a mensagem de sucesso. Caso não, retorna um dicionário com chave 'erro'
        e mensagem de erro. OBS: A função adiciona um número aleatório ao novo nome do arquivo
        para evitar conflitos de nomes iguais.
        '''
        resultado = {}
        if os.path.exists(caminho_atual) and os.path.exists(novo_caminho) and novo_nome != None:
            novo = novo_caminho + str(random.randint(1, 99)) + '_' + novo_nome
            os.rename(caminho_atual, novo)
            resultado['validado'] = f'Arquivo movido e renomeado!'

            return resultado
        
        else:
            resultado['erro'] = f'Operação de mover e renomear falhou'
            return resultado
        
        
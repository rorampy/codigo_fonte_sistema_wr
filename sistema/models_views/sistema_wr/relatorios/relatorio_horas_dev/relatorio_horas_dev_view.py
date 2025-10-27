import os
from sistema import app, db, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sistema._utilitarios import *
from sistema.models_views.sistema_wr.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.sistema_wr.gerenciar.projetos.lancamento_horas_model import LancamentoHorasModel
from sistema.models_views.sistema_wr.gerenciar.projetos.projeto_model import ProjetoModel
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel

@app.context_processor
def inject_relatorio_hora():
    dados_corretos = {}
    projetos = []
    usuarios = []
    try:
        if hasattr(current_user,'is_authenticated') and current_user.is_authenticated:
            projetos = ProjetoModel.listar_projetos_ativos()
            usuarios = UsuarioModel.obter_usuarios_desc_id()
    except:
        pass
    
    return {
        "dados_corretos": dados_corretos,
        "usuarios": usuarios,
        "projetos": projetos   
    }

@app.route('/relatorios/relatorio-horas-dev/exportar', methods=['GET','POST'])
@requires_roles
@login_required
def exportar_relatorio_horas_dev():
    try: 
        if request.method == 'GET':
            changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
            dataHoje = DataHora.obter_data_atual_padrao_br()

            dataInicio = request.args.get('data_inicio_horas_devs')
            dataFim = request.args.get('data_final_horas_devs')
            nomeDev = request.args.get('nomeDev')
            projetoDev = request.args.get('projetoDev')
            
            historicoHoras = LancamentoHorasModel.filtrar_horas_dev(dataInicio=dataInicio, dataFim=dataFim, nomeDev=nomeDev, projetoDev=projetoDev)


            logo_path = obter_url_absoluta_de_imagem("logo_relatorios.png")


            html=render_template(
                "relatorios/relatorio_horas_dev/relatorio_horas_devs.html",
                    logo_path=logo_path,
                    changelog=changelog, 
                    dataHoje=dataHoje, 
                    historicoHoras=historicoHoras
                )

            nome_arquivo_saida = f"relatorio_horas_dev-{dataHoje}"

            pdf = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

            return pdf

    except Exception as e:
        print('Algo deu errao ao exportar o relatório', e)
        flash(("Não foi possível gerar o relatório financeiro! Contate o suporte.", "warning"))
    
        return redirect(url_for("principal")) 
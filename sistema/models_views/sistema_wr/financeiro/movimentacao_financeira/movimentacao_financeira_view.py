import os
from sistema import app, db, requires_roles, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sistema._utilitarios import *
from sistema.models_views.sistema_wr.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo


@app.route('/movimentacao-financeira/listagem', methods=['GET'])
@requires_roles
@login_required
def movimentacao_financeira():
    
    filtros = {}
    dados_corretos = {}
    
    data_inicio = request.args.get('dataInicio', '').strip()
    data_fim = request.args.get('dataFim', '').strip()
    tipo_movimentacao = request.args.get('tipoMovimentacao', '').strip()
    categoria_id = request.args.get('categoriaId', '').strip()
    cliente_nome = request.args.get('clienteNome', '').strip()
    
    if data_inicio:
        filtros['data_inicio'] = data_inicio
    if data_fim:
        filtros['data_fim'] = data_fim
    if tipo_movimentacao:
        filtros['tipo_movimentacao'] = int(tipo_movimentacao)
    if categoria_id:
        filtros['categoria_id'] = int(categoria_id)
    if cliente_nome:
        filtros['cliente_nome'] = cliente_nome
    
    dados_corretos = request.args.to_dict()
    
    saldo_liquido = MovimentacaoFinanceiraModel.obter_valor_total_saldo_liquido_por_usuario()
    saldo_entradas = MovimentacaoFinanceiraModel.obter_valor_total_saldo_entradas_por_usuario()
    saldo_saidas = MovimentacaoFinanceiraModel.obter_valor_total_saldo_saidas_por_usuario()
    
    if filtros:
        movimentacao = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_com_filtros(filtros)
    else:
        movimentacao = MovimentacaoFinanceiraModel.listagem_movimentacoes_financeiras_por_usuario()
    
    inicializar_categorias_padrao()
    principais = CategoriaLancamentoModel.buscar_principais()
    estrutura = []
    for cat in principais:
        d = cat.to_dict()
        d["children"] = obter_subcategorias_recursivo(cat.id)
        estrutura.append(d)
    
    return render_template(
        'sistema_wr/financeiro/movimentacao_financeira/movimentacao_financeira.html', 
        saldo_liquido=saldo_liquido,
        saldo_entradas=saldo_entradas, 
        saldo_saidas=saldo_saidas, 
        movimentacao=movimentacao,
        estrutura=estrutura,
        dados_corretos=dados_corretos,
        filtros_ativos=bool(filtros)
    )

@app.route('/relatorios/relatorios-financeiros/exportar/movimentacao-financeira', methods=['GET','POST'])
@requires_roles
@login_required
def exportar_movimentacao_financeira():
    try: 
        changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
        dataHoje = DataHora.obter_data_atual_padrao_br()

        dataInicio = request.args.get('data_inicio_financeiro')
        dataFim = request.args.get('data_final_financeiro')
        
        filtro_movimentacao = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira(data_inicio=dataInicio, data_fim=dataFim)
        saldoEntrada = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira_saldo_entrada(data_inicio=dataInicio, data_fim=dataFim)
        print('Saldo entrada:', saldoEntrada)
        saldoSaida = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira_saldo_saida(data_inicio=dataInicio, data_fim=dataFim)
        print('Saldo entrada:', saldoSaida)
        saldoLiquido = MovimentacaoFinanceiraModel.filtrar_movimentacao_financeira_liquido(data_inicio=dataInicio, data_fim=dataFim)
        
        logo_path = obter_url_absoluta_de_imagem("/logo_wr_sem_fundo.png")

        html=render_template(
            "relatorios/relatorios_financeiros/relatorio_movimentacao_financeira.html",
            changelog = changelog, dataHoje = dataHoje, filtro_movimentacao = filtro_movimentacao, saldoEntrada = saldoEntrada,
            saldoSaida = saldoSaida, saldoLiquido = saldoLiquido, logo_path = logo_path
        )

        nome_arquivo_saida = f"relatorio_movimentacao_financeira-{dataHoje}"

        pdf = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

        return pdf

    except Exception as e:
        print('Algo deu errao ao exportar o relatório', e)
        flash(("Não foi possível gerar o relatório financeiro! Contate o suporte.", "warning"))
    
        return redirect(url_for("principal")) 
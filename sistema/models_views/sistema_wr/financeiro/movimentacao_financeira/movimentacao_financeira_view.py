import os
from sistema import app, db, requires_roles
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sistema._utilitarios import *


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
        'sistema_hash/financeiro/movimentacao_financeira/movimentacao_financeira.html', 
        saldo_liquido=saldo_liquido,
        saldo_entradas=saldo_entradas, 
        saldo_saidas=saldo_saidas, 
        movimentacao=movimentacao,
        estrutura=estrutura,
        dados_corretos=dados_corretos,
        filtros_ativos=bool(filtros)
    )
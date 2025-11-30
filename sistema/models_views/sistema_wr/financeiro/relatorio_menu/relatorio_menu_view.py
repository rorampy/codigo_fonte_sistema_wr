from sistema import app, requires_roles, obter_url_absoluta_de_imagem
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask_login import login_required
from flask import render_template, request, redirect, url_for, flash
from sistema.models_views.sistema_wr.financeiro.lancamento.lancamento_model import LancamentoModel
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.sistema_wr.configuracoes.gerais.plano_conta.plano_conta_model import PlanoContaModel
from sistema._utilitarios import ManipulacaoArquivos
from sistema import db
from sqlalchemy import desc, func, extract

@app.route('/relatorio_menu/demonstrativo_de_resultados', methods=['GET', 'POST'])
@login_required
@requires_roles
def demonstrativo_de_resultados():
    
    # Obter parâmetros de filtro
    mes = request.args.get('mes') or request.form.get('mes')
    ano = request.args.get('ano') or request.form.get('ano')
    
    # Se não houver filtro, usar o mês/ano mais recente com lançamentos
    if not mes or not ano:
        lancamento_mais_recente = LancamentoModel.query.filter(
            LancamentoModel.deletado == False,
            LancamentoModel.ativo == True,
            LancamentoModel.data_competencia.isnot(None)
        ).order_by(desc(LancamentoModel.data_competencia)).first()
        
        if lancamento_mais_recente and lancamento_mais_recente.data_competencia:
            data_referencia = lancamento_mais_recente.data_competencia
            mes = data_referencia.month
            ano = data_referencia.year
        else:
            hoje = datetime.now()
            mes = hoje.month
            ano = hoje.year
    else:
        mes = int(mes)
        ano = int(ano)
    
    # Definir período de competência
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - relativedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - relativedelta(days=1)
    
    # Buscar lançamentos por competência do período
    lancamentos = LancamentoModel.query.filter(
        LancamentoModel.deletado == False,
        LancamentoModel.ativo == True,
        LancamentoModel.data_competencia >= data_inicio,
        LancamentoModel.data_competencia <= data_fim
    ).all()
    
    # Organizar lançamentos por categoria do plano de contas
    dre_dados = calcular_dre(lancamentos)
    
    # Calcular saldos gerais
    saldo_entradas = sum(l.valor_lancamento_100 for l in lancamentos if l.tipo_lancamento == 1) or 0
    saldo_saidas = sum(l.valor_lancamento_100 for l in lancamentos if l.tipo_lancamento == 2) or 0
    saldo_liquido = saldo_entradas - saldo_saidas
    
    # Obter exercícios disponíveis para filtro
    exercicios = obter_exercicios_disponiveis()
    
    mes_string = str(mes)
    ano_string = str(ano)
    
    return render_template('relatorio_menu/demonstrativo_de_resultados.html', 
        mes_string=mes_string, 
        ano_string=ano_string,
        mes_atual=mes,
        ano_atual=ano,
        saldo_liquido=saldo_liquido,
        saldo_entradas=saldo_entradas, 
        saldo_saidas=saldo_saidas,
        dre_dados=dre_dados,
        exercicios=exercicios,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


@app.route('/relatorio_menu/dre/pdf', methods=['GET'])
@login_required
@requires_roles
def dre_pdf():
    """
    Gera o PDF do Demonstrativo de Resultados do Exercício
    """
    try:
        mes = request.args.get('mes')
        ano = request.args.get('ano')
        
        # Se não houver filtro, usar o mês/ano mais recente com lançamentos
        if not mes or not ano:
            lancamento_mais_recente = LancamentoModel.query.filter(
                LancamentoModel.deletado == False,
                LancamentoModel.ativo == True,
                LancamentoModel.data_competencia.isnot(None)
            ).order_by(desc(LancamentoModel.data_competencia)).first()
            
            if lancamento_mais_recente and lancamento_mais_recente.data_competencia:
                data_referencia = lancamento_mais_recente.data_competencia
                mes = data_referencia.month
                ano = data_referencia.year
            else:
                hoje = datetime.now()
                mes = hoje.month
                ano = hoje.year
        else:
            mes = int(mes)
            ano = int(ano)
        
        # Definir período de competência
        data_inicio = date(ano, mes, 1)
        if mes == 12:
            data_fim = date(ano + 1, 1, 1) - relativedelta(days=1)
        else:
            data_fim = date(ano, mes + 1, 1) - relativedelta(days=1)
        
        # Buscar lançamentos por competência do período
        lancamentos = LancamentoModel.query.filter(
            LancamentoModel.deletado == False,
            LancamentoModel.ativo == True,
            LancamentoModel.data_competencia >= data_inicio,
            LancamentoModel.data_competencia <= data_fim
        ).all()
        
        # Organizar lançamentos por categoria do plano de contas
        dre_dados = calcular_dre(lancamentos)
        
        # Calcular saldos
        saldo_entradas = sum(l.valor_lancamento_100 for l in lancamentos if l.tipo_lancamento == 1) or 0
        saldo_saidas = sum(l.valor_lancamento_100 for l in lancamentos if l.tipo_lancamento == 2) or 0
        
        # Formatar strings
        mes_string = f"{mes:02d}"
        ano_string = str(ano)
        data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Obter logo do sistema
        logo_path = obter_url_absoluta_de_imagem("logo_relatorios.png")
        
        # Renderizar template do PDF
        html = render_template(
            'relatorio_layout/dre_pdf.html',
            mes_string=mes_string,
            ano_string=ano_string,
            dre_dados=dre_dados,
            saldo_entradas=saldo_entradas,
            saldo_saidas=saldo_saidas,
            data_geracao=data_geracao,
            logo_path=logo_path
        )
        
        # Gerar nome do arquivo
        nome_arquivo = f"DRE_{mes_string}_{ano_string}"
        
        # Gerar PDF
        pdf = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo)
        
        return pdf
        
    except Exception as e:
        print(f'Erro ao gerar PDF do DRE: {e}')
        flash(("Não foi possível gerar o PDF do DRE! Contate o suporte.", "warning"))
        return redirect(url_for("demonstrativo_de_resultados"))


def calcular_dre(lancamentos):
    """
    Calcula o Demonstrativo de Resultados do Exercício
    organizado por categorias do plano de contas
    """
    # Estrutura do DRE
    dre = {
        'receitas': {
            'total': 0,
            'categorias': {}
        },
        'despesas': {
            'total': 0,
            'categorias': {}
        },
        'lucro_bruto': 0,
        'lucro_operacional': 0,
        'resultado_liquido': 0,
        'detalhes': []
    }
    
    for lancamento in lancamentos:
        valor = lancamento.valor_lancamento_100 or 0
        categoria = lancamento.categoria
        
        if lancamento.tipo_lancamento == 1:  # Entrada/Receita
            dre['receitas']['total'] += valor
            
            if categoria:
                cat_codigo = categoria.codigo
                cat_nome = categoria.nome
                
                # Buscar categoria pai para agrupamento
                cat_pai = obter_categoria_pai_principal(categoria)
                grupo_nome = cat_pai.nome if cat_pai else cat_nome
                grupo_codigo = cat_pai.codigo if cat_pai else cat_codigo
                
                if grupo_codigo not in dre['receitas']['categorias']:
                    dre['receitas']['categorias'][grupo_codigo] = {
                        'nome': grupo_nome,
                        'codigo': grupo_codigo,
                        'total': 0,
                        'subcategorias': {}
                    }
                
                dre['receitas']['categorias'][grupo_codigo]['total'] += valor
                
                # Adicionar subcategoria
                if cat_codigo not in dre['receitas']['categorias'][grupo_codigo]['subcategorias']:
                    dre['receitas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo] = {
                        'nome': cat_nome,
                        'codigo': cat_codigo,
                        'total': 0,
                        'lancamentos': []
                    }
                
                dre['receitas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo]['total'] += valor
                dre['receitas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo]['lancamentos'].append({
                    'descricao': lancamento.descricao,
                    'valor': valor,
                    'data': lancamento.data_competencia
                })
            else:
                # Sem categoria
                if 'sem_categoria' not in dre['receitas']['categorias']:
                    dre['receitas']['categorias']['sem_categoria'] = {
                        'nome': 'Outras Receitas',
                        'codigo': '0',
                        'total': 0,
                        'subcategorias': {}
                    }
                dre['receitas']['categorias']['sem_categoria']['total'] += valor
                
        elif lancamento.tipo_lancamento == 2:  # Saída/Despesa
            dre['despesas']['total'] += valor
            
            if categoria:
                cat_codigo = categoria.codigo
                cat_nome = categoria.nome
                
                # Buscar categoria pai para agrupamento
                cat_pai = obter_categoria_pai_principal(categoria)
                grupo_nome = cat_pai.nome if cat_pai else cat_nome
                grupo_codigo = cat_pai.codigo if cat_pai else cat_codigo
                
                if grupo_codigo not in dre['despesas']['categorias']:
                    dre['despesas']['categorias'][grupo_codigo] = {
                        'nome': grupo_nome,
                        'codigo': grupo_codigo,
                        'total': 0,
                        'subcategorias': {}
                    }
                
                dre['despesas']['categorias'][grupo_codigo]['total'] += valor
                
                # Adicionar subcategoria
                if cat_codigo not in dre['despesas']['categorias'][grupo_codigo]['subcategorias']:
                    dre['despesas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo] = {
                        'nome': cat_nome,
                        'codigo': cat_codigo,
                        'total': 0,
                        'lancamentos': []
                    }
                
                dre['despesas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo]['total'] += valor
                dre['despesas']['categorias'][grupo_codigo]['subcategorias'][cat_codigo]['lancamentos'].append({
                    'descricao': lancamento.descricao,
                    'valor': valor,
                    'data': lancamento.data_competencia
                })
            else:
                # Sem categoria
                if 'sem_categoria' not in dre['despesas']['categorias']:
                    dre['despesas']['categorias']['sem_categoria'] = {
                        'nome': 'Outras Despesas',
                        'codigo': '0',
                        'total': 0,
                        'subcategorias': {}
                    }
                dre['despesas']['categorias']['sem_categoria']['total'] += valor
    
    # Calcular resultados
    dre['lucro_bruto'] = dre['receitas']['total'] - dre['despesas']['total']
    dre['lucro_operacional'] = dre['lucro_bruto']  # Pode ser ajustado com despesas operacionais específicas
    dre['resultado_liquido'] = dre['lucro_operacional']  # Pode ser ajustado com impostos, etc.
    
    return dre


def obter_categoria_pai_principal(categoria):
    """
    Retorna a categoria pai de nível 2 (subcategoria direta da principal)
    para agrupamento no DRE
    """
    if not categoria:
        return None
    
    if categoria.nivel <= 2:
        return categoria
    
    # Buscar pai recursivamente até nível 2
    atual = categoria
    while atual.parent_id and atual.nivel > 2:
        atual = PlanoContaModel.query.get(atual.parent_id)
        if not atual:
            break
    
    return atual


def obter_exercicios_disponiveis():
    """
    Retorna lista de exercícios (mês/ano) disponíveis baseado nos lançamentos
    """
    lancamentos = LancamentoModel.query.filter(
        LancamentoModel.deletado == False,
        LancamentoModel.ativo == True,
        LancamentoModel.data_competencia.isnot(None)
    ).with_entities(
        extract('month', LancamentoModel.data_competencia).label('mes'),
        extract('year', LancamentoModel.data_competencia).label('ano')
    ).distinct().order_by(
        desc(extract('year', LancamentoModel.data_competencia)),
        desc(extract('month', LancamentoModel.data_competencia))
    ).all()
    
    exercicios = []
    for l in lancamentos:
        mes = int(l.mes)
        ano = int(l.ano)
        exercicio = f"{mes:02d}/{ano}"
        if exercicio not in exercicios:
            exercicios.append(exercicio)
    
    return exercicios

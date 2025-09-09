from sistema import app, requires_roles, db, current_user, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sistema._utilitarios import *
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.sistema_wr.financeiro.recebimento.recebimento_model import RecebimentoModel
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo

@app.route('/lancamentos-receber', methods=['GET'])
@login_required
@requires_roles
def lancamentos_receber():
    try:
        recebimento = RecebimentoModel.listar_a_receber_agrupado_por_cliente()
        return render_template('sistema_wr/financeiro/recebimento/lancamentos_receber.html', recebimento=recebimento)
    except Exception as e:
        print("Erro ao listar lançamentos a receber:", e)
        flash(("Erro ao listar lançamentos a receber.", "danger"))
        return render_template('sistema_wr/financeiro/recebimento/lancamentos_receber.html', recebimento=[])


@app.route('/lancamentos-receber/informar-recebimento/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def informar_recebimento(id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        inicializar_categorias_padrao()
        principais = CategoriaLancamentoModel.buscar_principais()
        estrutura = []
        for cat in principais:
            d = cat.to_dict()
            d["children"] = obter_subcategorias_recursivo(cat.id)
            estrutura.append(d)

        recebimento = RecebimentoModel.obter_recebimento_por_id(id)

        if not recebimento:
            flash(("Recebimento não encontrado.", "warning"))
            return redirect(url_for('lancamentos_receber'))
        
        if recebimento.status_id == 2:
            flash(('Recebimento já consta como pago.', 'warning'))
            return redirect(url_for('lancamentos_receber'))

        if request.method == 'POST':
            campos = {
                'dataPagamento': ['Data do Pagamento', request.form.get('dataPagamento')],
                'categorizacao_fiscal': ['Categorização Fiscal', request.form.get('categorizacao_fiscal')],
                'valorRecebimento': ['Valor Recebido', request.form.get('valorRecebimento')],
            }
            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
            if not "validado" in validacao_campos_obrigatorios:
                print(validacao_campos_obrigatorios)
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                valor_monetario_formatado = ValoresMonetarios.converter_string_brl_para_float(request.form.get('valorRecebimento')) * 100
                recebimento.data_pagamento = request.form.get('dataPagamento')
                recebimento.valor_pago = valor_monetario_formatado
                recebimento.categoria_lancamento_id = request.form.get('categorizacao_fiscal')
                recebimento.status_id = 2 # Recebido
                recebimento.observacao = (
                    f"Recebimento {recebimento.cliente.identificacao} - {recebimento.contrato_produto.produto.descricao if recebimento.contrato_produto and recebimento.contrato_produto.produto else '-'}"
                )
                comprovante = request.files.get('comprovante_recebimento')
                if comprovante and comprovante.filename:
                    if comprovante.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                        comprovante_obj = upload_arquivo(
                            comprovante, "UPLOAD_COMPROVANTE_RECEBIMENTO", f"comprovante_recebimento_{recebimento.id}"
                        )
                        recebimento.comprovante_id = comprovante_obj.id
                    else:
                        flash(("O comprovante deve estar em formato JPG, JPEG, PNG ou PDF.", "warning"))
                        return redirect(url_for("informar_recebimento", id=recebimento.id))

                # Cadastro na movimentação financeira
                MovimentacaoFinanceiraModel.cadastrar_movimentacao_financeira(tipo_movimentacao=1, valor_movimentacao=valor_monetario_formatado,
                    data_movimentacao=recebimento.data_pagamento, recebimento_id=recebimento.id
                )
                
                db.session.commit()
                flash(("Recebimento informado com sucesso!", "success"))
                return redirect(url_for('lancamentos_receber'))

        return render_template('sistema_wr/financeiro/recebimento/informar_recebimento.html', recebimento=recebimento, dados_corretos=request.form,
                        campos_obrigatorios=validacao_campos_obrigatorios,
                        campos_erros=validacao_campos_erros, estrutura=estrutura)
    except Exception as e:
        print("Erro ao informar recebimento:", e)
        flash(("Erro ao informar recebimento.", "danger"))
    return redirect(url_for('lancamentos_receber'))


@app.route('/lancamentos-receber/cancelar-informe-recebimento/<int:id>', methods=['GET', 'POST'])
@login_required
@requires_roles
def cancelar_informe_recebimento(id):
    try:
        dataHoje = DataHora.obter_data_atual_padrao_en()
        recebimento = RecebimentoModel.obter_recebimento_por_id(id)

        if not recebimento:
            flash(("Recebimento não encontrado.", "warning"))
            return redirect(url_for('lancamentos_receber'))
        
        if recebimento.status_id != 2:
            flash(('Recebimento não consta como recebido!.', 'warning'))
            return redirect(url_for('lancamentos_receber'))
        
        # Cadastro na movimentação financeira, tipo estorno
        MovimentacaoFinanceiraModel.cadastrar_movimentacao_financeira(tipo_movimentacao=4, valor_movimentacao=recebimento.valor_pago,
            data_movimentacao=dataHoje, recebimento_id=recebimento.id
        )

        recebimento.data_pagamento = None
        recebimento.valor_pago = None
        recebimento.status_id = 5  # Aguardando Pagamento
        recebimento.comprovante_id = None
        recebimento.categoria_lancamento_id = None

        db.session.commit()

        flash(("Recebimento cancelado com sucesso!", "success"))
        return redirect(url_for('lancamentos_receber'))

    except Exception as e:
        print("Erro ao informar recebimento:", e)
        flash(("Erro ao informar recebimento.", "danger"))
    return redirect(url_for('lancamentos_receber'))
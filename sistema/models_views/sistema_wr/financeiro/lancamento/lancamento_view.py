import os
from sistema import app, db, requires_roles
from logs_sistema import flask_logger
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sistema.models_views.sistema_wr.financeiro.lancamento.lancamento_model import LancamentoModel
from sistema.models_views.sistema_wr.financeiro.movimentacao_financeira.movimentacao_financeira_model import MovimentacaoFinanceiraModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_view import inicializar_categorias_padrao, obter_subcategorias_recursivo
from sistema.models_views.sistema_wr.configuracoes.gerais.categoria_lancamento.categoria_lancamento_model import CategoriaLancamentoModel
from sistema._utilitarios import *


@app.route('/financeiro/lancamentos/listagem', methods=['GET', 'POST'])
@requires_roles
@login_required
def lancamentos_financeiros():
    lancamentos = LancamentoModel.lancamentos_ativos_usuario()
    return render_template('sistema_wr/financeiro/lancamentos/lancamento_listagem.html',
                           lancamentos=lancamentos)

@app.route('/financeiro/cadastrar/lancamento', methods=['GET', 'POST'])
@requires_roles
@login_required
def cadastrar_lancamento():
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
        print(estrutura)

        if request.method == 'POST':
            tipoLancamento = request.form['tipoLancamento']
            categoriaLancamento = request.form['categoriaLancamento']
            dataLancamento = request.form['dataLancamento']
            valorLancamento = request.form['valorLancamento']
            descricaoLancamento = request.form['descricaoLancamento']
            comprovanteLancamentoSaida = request.files.get('comprovanteLancamentoSaida')


            campos = {
                'tipoLancamento': ['Tipo Lançamento', tipoLancamento],
                'categoriaLancamento': ['Categoria', categoriaLancamento],
                'dataLancamento': ['Data lançamento', dataLancamento],
                'valorLancamento': ['Valor', valorLancamento],
                'descricaoLancamento': ['Descrição', descricaoLancamento],
            }

            if tipoLancamento == '2':
                campos['comprovanteLancamentoSaida'] = ['Comprovante', comprovanteLancamentoSaida]

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))
            
            if gravar_banco:
                valor_monetario_formatado = (ValoresMonetarios.converter_string_brl_para_float(valorLancamento) * 100)
                
                lancamento = LancamentoModel(
                    despesa_recorrente=0,
                    tipo_lancamento=int(tipoLancamento),
                    categoria_id=int(categoriaLancamento),
                    data_movimentacao=dataLancamento,
                    descricao=descricaoLancamento,
                    valor_lancamento_100=valor_monetario_formatado,
                )
                db.session.add(lancamento)
                db.session.flush()

                if lancamento.tipo_lancamento == 2:
                    if comprovanteLancamentoSaida and comprovanteLancamentoSaida.filename:
                        if comprovanteLancamentoSaida.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                            comprovante = upload_arquivo(
                                comprovanteLancamentoSaida, "UPLOAD_COMPROVANTE_LANCAMENTO_SAIDA", f"comprovante_saida_{lancamento.id}"
                            )
                            lancamento.comprovante_id = comprovante.id
                        else:
                            flash(("O comprovante deve estar em formato JPG, JPEG, PNG ou PDF.", "warning"))
                            return redirect(url_for("cadastrar_lancamento"))
                
                MovimentacaoFinanceiraModel.cadastrar_movimentacao_financeira(tipo_movimentacao=lancamento.tipo_lancamento, valor_movimentacao=lancamento.valor_lancamento_100,
                    data_movimentacao=lancamento.data_movimentacao, lancamento_id=lancamento.id
                )

                db.session.commit()
                flash(('Lançamento cadastrado com sucesso!', 'success'))
                return redirect(url_for('lancamentos_financeiros'))

    except Exception as e:
        print(f'[ERRO] Erro ao tentar criar um lançamento! : {e}')
        flash(('Houve um erro ao tentar cadastrar lançamento! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('lancamentos_financeiros'))
    return render_template('sistema_wr/financeiro/lancamentos/lancamento_cadastrar.html', dados_corretos=request.form,
                           campos_obrigatorios=validacao_campos_obrigatorios,
                           campos_erros=validacao_campos_erros, estrutura=estrutura)

@app.route('/financeiro/editar/lancamento/<int:id>', methods=['GET', 'POST'])
@requires_roles
@login_required
def editar_lancamento(id):
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

        lancamento = LancamentoModel.obter_lancamento_usuario(id)

        if not lancamento:
            flash(('Lançamento nâo encontrado! Tente novamente mais tarde.', 'warning'))
            return redirect(url_for('lancamentos_financeiros'))
        
        dados_corretos = {
            'tipoLancamento': lancamento.tipo_lancamento,
            'categoriaLancamento': lancamento.categoria_id,
            'dataLancamento': lancamento.data_movimentacao,
            'valorLancamento': lancamento.valor_lancamento_100,
            'descricaoLancamento': lancamento.descricao
        }

        if request.method == 'POST':
            tipoLancamento = request.form['tipoLancamento']
            categoriaLancamento = request.form['categoriaLancamento']
            dataLancamento = request.form['dataLancamento']
            valorLancamento = request.form['valorLancamento']
            descricaoLancamento = request.form['descricaoLancamento']
            comprovanteLancamentoSaida = request.files.get('comprovanteLancamentoSaida')
            opcaoComprovante = request.form.get('opcaoComprovante', 'manter')

            campos = {
                'tipoLancamento': ['Tipo Lançamento', tipoLancamento],
                'categoriaLancamento': ['Categoria', categoriaLancamento],
                'dataLancamento': ['Data lançamento', dataLancamento],
                'valorLancamento': ['Valor', valorLancamento],
                'descricaoLancamento': ['Descrição', descricaoLancamento],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))
            
            if gravar_banco:
                valor_monetario_formatado = (ValoresMonetarios.converter_string_brl_para_float(valorLancamento) * 100)
                
                lancamento.tipo_lancamento=int(tipoLancamento)
                lancamento.categoria_id=int(categoriaLancamento)
                lancamento.data_movimentacao=dataLancamento
                lancamento.descricao=descricaoLancamento
                lancamento.valor_lancamento_100=valor_monetario_formatado                    

                db.session.flush()

                if lancamento.tipo_lancamento == 2 and opcaoComprovante == 'alterar':
                    if comprovanteLancamentoSaida and comprovanteLancamentoSaida.filename:
                        if comprovanteLancamentoSaida.mimetype in ["application/pdf", "image/jpeg", "image/png"]:
                            comprovante = upload_arquivo(
                                comprovanteLancamentoSaida, "UPLOAD_COMPROVANTE_LANCAMENTO_SAIDA", f"comprovante_saida_{lancamento.id}"
                            )
                            lancamento.comprovante_id = comprovante.id
                        else:
                            flash(("O comprovante deve estar em formato JPG, JPEG, PNG ou PDF.", "warning"))
                            return redirect(url_for("editar_lancamento", id=id))
                        
                movimentacao = MovimentacaoFinanceiraModel.obter_movimentacao_por_usuario_lancamento(lancamento.id)

                if not movimentacao:
                    MovimentacaoFinanceiraModel.cadastrar_movimentacao_financeira(
                        tipo_movimentacao=int(tipoLancamento), valor_movimentacao=valor_monetario_formatado,
                        data_movimentacao=dataLancamento, lancamento_id=lancamento.id
                    )
                else:
                    movimentacao.valor_movimentacao_100 = valor_monetario_formatado
                    movimentacao.tipo_movimentacao = int(tipoLancamento)
                    movimentacao.data_movimentacao = dataLancamento

                db.session.commit()
                flash(('Lançamento editado com sucesso!', 'success'))
                return redirect(url_for('lancamentos_financeiros'))

    except Exception as e:
        print(f'[ERRO] Erro ao tentar editar lançamento! : {e}')
        flash(('Houve um erro ao tentar editar lançamento! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('lancamentos_financeiros'))

    return render_template('sistema_wr/financeiro/lancamentos/lancamento_editar.html', dados_corretos=dados_corretos,
                           campos_obrigatorios=validacao_campos_obrigatorios,
                           campos_erros=validacao_campos_erros, lancamento=lancamento, estrutura=estrutura)

@app.route('/financeiro/excluir/lancamento/<int:id>', methods=['GET', 'POST'])
@requires_roles
@login_required
def excluir_lancamento(id):
    try:
        lancamento = LancamentoModel.obter_lancamento_usuario(id)

        if not lancamento:
            flash(('Lançamento nâo encontrado! Tente novamente mais tarde.', 'warning'))
            return redirect(url_for('lancamentos_financeiros'))

        lancamento.deletado = True
        lancamento.ativo = False

        movimentacao = MovimentacaoFinanceiraModel.obter_movimentacao_por_usuario_lancamento(lancamento.id)

        movimentacao.ativo = False
        movimentacao.deletado = True

        db.session.commit()

        flash(('Lançamento excluido com sucesso!', 'success'))
        return redirect(url_for('lancamentos_financeiros'))

    except Exception as e:
        print(f'[ERRO] Erro ao tentar excluir um lançamento! : {e}')
        flash(('Houve um erro ao tentar excluir este lançamento! Entre em contato com o suporte.', 'warning'))
    return redirect(url_for('lancamentos_financeiros'))
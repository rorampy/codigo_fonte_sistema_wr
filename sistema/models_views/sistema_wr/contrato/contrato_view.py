from sistema import app, requires_roles, db, current_user, obter_url_absoluta_de_imagem
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from sistema._utilitarios import *
from sistema.models_views.sistema_wr.contrato.contrato_model import ContratoModel
from sistema.models_views.sistema_wr.contrato.contrato_produto import ContratoProduto
from sistema.models_views.sistema_wr.gerenciar.clientes.cliente_model import ClienteModel
from sistema.models_views.sistema_wr.gerenciar.produtos.produto_model import ProdutoModel
from sistema.models_views.sistema_wr.configuracoes.gerais.modelo_contrato.modelo_contrato_model import ModeloContratoModel
from sistema.models_views.sistema_wr.parametrizacao.forma_pagamento_model import FormaPagamentoModel
from sistema.models_views.sistema_wr.parametrizacao.changelog_model import ChangelogModel
from sistema.models_views.sistema_wr.parametrizacao.variavel_sistema_model import VariavelSistemaModel
from sistema.models_views.sistema_wr.financeiro.recebimento.recebimento_model import RecebimentoModel
from sistema.models_views.upload_arquivo.upload_arquivo_view import upload_arquivo

@app.route("/contrato/listar", methods=["GET"])
@login_required
@requires_roles
def contrato_listar():
    try:
        contratos = ContratoModel.listar_contratos_ativos()
    except Exception as e:
        print(f"Erro ao listar contratos: {str(e)}")
        flash((f"Erro ao listar contratos!", "danger"))
        return render_template("sistema_hash/financeiro/contrato/contrato_listar.html", contratos=[])
    return render_template(
        "sistema_hash/financeiro/contrato/contrato_listar.html",
        contratos=contratos
    )

@app.route("/contrato/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def contrato_cadastrar():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    dados_corretos = request.form.to_dict() if request.method == "POST" else {}

    clientes = ClienteModel.listar_clientes_ativos()
    produtos = ProdutoModel.listar_produtos_ativos()
    modelo_contrato = ModeloContratoModel.obter_modelos_contratos_ativos()
    formas_pagamento = FormaPagamentoModel.listar_formas_pagamento()

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        tipo_contrato = request.form.get("tipo_contrato")
        vigencia_inicio = request.form.get("vigencia_inicio")
        vigencia_fim = request.form.get("vigencia_fim")
        status_contrato = request.form.get("status_contrato")
        observacoes = request.form.get("observacoes")

        produto_id = request.form.get("produto_id")
        valor_negociado = request.form.get("valor_negociado")
        forma_pagamento_id = request.form.get("forma_pagamento")
        cartao_credito = True if forma_pagamento_id == '2' else False
        nmro_parcelas = request.form.get("numero_parcelas") if forma_pagamento_id == '2' else None

        campos = {
            "cliente_id": ["Cliente", cliente_id],
            "produto_id": ["Produto", produto_id],
            "tipo_contrato": ["Modelo de Contrato", tipo_contrato],
            "vigencia_inicio": ["Vigência Início", vigencia_inicio],
            "status_contrato": ["Status", status_contrato]
        }
        if forma_pagamento_id == '2':
            campos["numero_parcelas"] = ["Número de Parcelas", nmro_parcelas]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        verifica_contrato = ContratoModel.obter_contrato_por_cliente_produto_contrato(cliente_id, produto_id, tipo_contrato)
        if verifica_contrato:
            gravar_banco = False
            flash(("Já existe um contrato ativo para este cliente, produto e contrato!", "warning"))
        
        data_atual = DataHora.obter_data_atual_padrao_en()

        if vigencia_inicio < data_atual:
            flash(("A vigência de início não pode ser anterior à data atual!", "warning"))
            gravar_banco = False

        if gravar_banco:
            try:
                contrato = ContratoModel(
                    cliente_id=cliente_id,
                    forma_pagamento_id=forma_pagamento_id,
                    modelo_contrato_id=tipo_contrato,
                    observacoes=observacoes,
                    ativo=True,
                    status_contrato=status_contrato
                )
                db.session.add(contrato)
                db.session.flush()

                cliente = ClienteModel.obter_cliente_por_id(cliente_id)
                produto = ProdutoModel.obter_produto_id(produto_id)

                contrato_produto = ContratoProduto(
                    contrato_id=contrato.id,
                    produto_id=produto_id,
                    vigencia_inicio=vigencia_inicio,
                    vigencia_fim=vigencia_fim if vigencia_fim else None,
                    valor_negociado=int(ValoresMonetarios.converter_string_brl_para_float(valor_negociado) * 100) if valor_negociado else None,
                    cartao_credito=cartao_credito,
                    nmro_parcelas=nmro_parcelas,
                    observacoes=observacoes
                )
                db.session.add(contrato_produto)
                db.session.flush()

                if status_contrato == '1': # Status ativo
                    valor_recebimento = contrato_produto.valor_negociado if contrato_produto.valor_negociado and contrato_produto.valor_negociado != 0 else produto.valor
                    RecebimentoModel.gerar_recebimentos_contrato_periodo(
                        contrato,
                        contrato_produto,
                        cliente,
                        produto,
                        valor_recebimento
                    )

                db.session.commit()
                flash(("Contrato cadastrado com sucesso!", "success"))
                return redirect(url_for('contrato_listar'))
            except Exception as e: 
                db.session.rollback()
                print(e)
                flash((f"Erro ao cadastrar contrato: {str(e)}", "danger"))
                gravar_banco = False

    return render_template(
        "sistema_hash/financeiro/contrato/contrato_cadastrar.html",
        clientes=clientes,
        produtos=produtos,
        modelo_contrato=modelo_contrato,
        formas_pagamento=formas_pagamento,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )


@app.route("/contrato/editar/<int:contrato_id>", methods=["GET", "POST"])
@login_required
@requires_roles
def contrato_editar(contrato_id):
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    contrato = ContratoModel.obter_contrato_id(contrato_id)
    contrato_produto = ContratoProduto.obter_contrato_por_id(contrato_id)

    if not contrato or not contrato_produto or not contrato.ativo:
        flash(("Contrato não encontrado ou inativo!", "danger"))
        return redirect(url_for('contrato_listar'))

    clientes = ClienteModel.listar_clientes_ativos()
    produtos = ProdutoModel.listar_produtos_ativos()
    modelo_contrato = ModeloContratoModel.obter_modelos_contratos_ativos()
    formas_pagamento = FormaPagamentoModel.listar_formas_pagamento()
    
    if request.method == "GET":
        dados_corretos = {
            "cliente_id": str(contrato.cliente_id),
            "produto_id": str(contrato_produto.produto_id) if contrato_produto else "",
            "tipo_contrato": str(contrato.modelo_contrato_id) if contrato.modelo_contrato_id else "",
            "vigencia_inicio": contrato_produto.vigencia_inicio if contrato_produto and contrato_produto.vigencia_inicio else "",
            "vigencia_fim": contrato_produto.vigencia_fim if contrato_produto and contrato_produto.vigencia_fim else "",
            "status_contrato": str(contrato.status_contrato) if contrato.status_contrato else "",
            "valor_negociado": str(contrato_produto.valor_negociado) if contrato_produto and contrato_produto.valor_negociado else "",
            "forma_pagamento": str(contrato.forma_pagamento_id) if contrato.forma_pagamento_id else "",
            "numero_parcelas": str(contrato_produto.nmro_parcelas) if contrato_produto and contrato_produto.nmro_parcelas else "",
            "observacoes": contrato_produto.observacoes if contrato_produto and contrato_produto.observacoes else ""
        }
    else:
        dados_corretos = request.form.to_dict()


    if request.method == "POST":
        cliente_id = request.form.get("cliente_id")
        produto_id = request.form.get("produto_id")
        tipo_contrato = request.form.get("tipo_contrato")
        vigencia_inicio = request.form.get("vigencia_inicio")
        vigencia_fim = request.form.get("vigencia_fim")
        status_contrato = request.form.get("status_contrato")
        observacoes = request.form.get("observacoes")
        
        valor_negociado = request.form.get("valor_negociado")
        forma_pagamento_id = request.form.get("forma_pagamento")
        cartao_credito = True if forma_pagamento_id == '2' else False
        nmro_parcelas = request.form.get("numero_parcelas") if forma_pagamento_id == '2' else None

        campos = {
            "cliente_id": ["Cliente", cliente_id],
            "produto_id": ["Produto", produto_id],
            "tipo_contrato": ["Modelo de Contrato", tipo_contrato],
            "vigencia_inicio": ["Vigência Início", vigencia_inicio],
            "status_contrato": ["Status", status_contrato]
        }
        
        if forma_pagamento_id == '2':
            campos["numero_parcelas"] = ["Número de Parcelas", nmro_parcelas]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash(("Verifique os campos destacados em vermelho!", "warning"))

        verifica_contrato = ContratoModel.obter_contrato_por_cliente_produto_contrato(cliente_id, produto_id, tipo_contrato)
        if verifica_contrato and verifica_contrato.id != contrato.id:
            gravar_banco = False
            flash(("Já existe um contrato ativo para este cliente, produto e contrato!", "warning"))

        if gravar_banco:
            try:
                contrato.cliente_id = cliente_id
                contrato.data_inicio = vigencia_inicio
                contrato.forma_pagamento_id = forma_pagamento_id
                contrato.modelo_contrato_id = tipo_contrato
                contrato.observacoes = observacoes
                contrato.status_contrato = status_contrato

                if contrato_produto:
                    contrato_produto.produto_id = produto_id
                    contrato_produto.vigencia_inicio = vigencia_inicio
                    contrato_produto.vigencia_fim = vigencia_fim if vigencia_fim else None
                    contrato_produto.valor_negociado = int(ValoresMonetarios.converter_string_brl_para_float(valor_negociado) * 100) if valor_negociado else None
                    contrato_produto.cartao_credito = cartao_credito
                    contrato_produto.nmro_parcelas = nmro_parcelas
                    contrato_produto.observacoes = observacoes
                else:
                    contrato_produto = ContratoProduto(
                        contrato_id=contrato.id,
                        produto_id=produto_id,
                        vigencia_inicio=vigencia_inicio,
                        vigencia_fim=vigencia_fim if vigencia_fim else None,
                        valor_negociado=int(ValoresMonetarios.converter_string_brl_para_float(valor_negociado) * 100) if valor_negociado else None,
                        cartao_credito=cartao_credito,
                        nmro_parcelas=nmro_parcelas,
                        observacoes=observacoes
                    )
                    db.session.add(contrato_produto)
                    db.session.flush()

                verifica_recebimento = RecebimentoModel.buscar_recebimentos_por_contrato(contrato.id)
                if not verifica_recebimento:
                    if status_contrato == '1': # Status ativo
                        valor_recebimento = contrato_produto.valor_negociado if contrato_produto.valor_negociado and contrato_produto.valor_negociado != 0 else contrato_produto.produto.valor
                        RecebimentoModel.gerar_recebimentos_contrato_periodo(
                            contrato,
                            contrato_produto,
                            contrato.cliente,
                            contrato_produto.produto,
                            valor_recebimento
                        )
                
                db.session.commit()
                flash(("Contrato atualizado com sucesso!", "success"))
                return redirect(url_for('contrato_listar'))
                
            except Exception as e:
                db.session.rollback()
                flash((f"Erro ao atualizar contrato: {str(e)}", "danger"))
                gravar_banco = False

    return render_template(
        "sistema_hash/financeiro/contrato/contrato_editar.html",
        contrato=contrato,
        contrato_produto=contrato_produto,
        clientes=clientes,
        produtos=produtos,
        modelo_contrato=modelo_contrato,
        forma_pagamento=formas_pagamento,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )

@app.route("/contrato/excluir/<int:contrato_id>", methods=["POST"])
@login_required
@requires_roles
def contrato_excluir(contrato_id):
    try:
        contrato = ContratoModel.obter_contrato_id(contrato_id)

        if not contrato or not contrato.ativo:
            flash(("Contrato não encontrado!", "danger"))
            return redirect(url_for('contrato_listar'))
    
        # Exclui os produtos vinculados ao contrato
        contrato.ativo = False
        contrato.deletado = True

        for contrato_produto in contrato.contrato_produto:
            contrato_produto.deletado = True
            contrato_produto.ativo = False
        db.session.commit()
        flash(("Contrato excluído com sucesso!", "success"))
    except Exception as e:
        db.session.rollback()
        flash((f"Erro ao excluir contrato: {str(e)}", "danger"))
    return redirect(url_for('contrato_listar'))


@app.route("/contrato/exportar-contrato/<int:id>", methods=["GET", "POST"])
@requires_roles
@login_required
def contrato_exportar_pdf(id):
    contrato = ContratoModel.obter_contrato_id(id)
    variaveis_sistema = VariavelSistemaModel.obter_variaveis_de_sistema_por_id(1)

    if not contrato:
        flash(("Contrato informado não encontrado!", "warning"))
        return redirect(url_for("contrato_listar"))

    conteudo_processado = ""
    if contrato.modelo_contrato:
        conteudo_processado = ProcessadorVariaveisContrato.substituir_variaveis(
            contrato.modelo_contrato.conteudo,
            contrato
        )

    dataHoje = DataHora.obter_data_atual_padrao_br()
    changelog = ChangelogModel.obter_numero_versao_changelog_mais_recente()
    logo_path = obter_url_absoluta_de_imagem("logo.png")

    html = render_template(
        "sistema_hash/financeiro/contrato/layout_contrato/layout_contrato.html",
        logo_path=logo_path,
        dataHoje=dataHoje,
        changelog=changelog,
        contrato=contrato,
        modeloContrato=contrato.modelo_contrato,
        conteudo_contrato=conteudo_processado,
        variaveis_sistema=variaveis_sistema
    )

    nome_arquivo_saida = f"contrato_{contrato.cliente.identificacao}-{dataHoje}"
    resposta = ManipulacaoArquivos.gerar_pdf_from_html(html, nome_arquivo_saida)

    return resposta

@app.route("/contratos/enviar-contrato-assinado/<int:id>", methods=["GET", "POST"])
@requires_roles
@login_required
def cadastrar_contrato_assinado(id):
    try:
        dados_corretos = request.form
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        contrato = ContratoModel.obter_contrato_id(id)
        dataHoje = DataHora.obter_data_atual_padrao_en()

        if not contrato:
            flash(("Contrato não encontrado!", "warning"))
            return redirect(url_for("contrato_listar"))

        if contrato.status_contrato != 1:
            flash(("Contrato não está ativo!", "warning"))
            return redirect(url_for("contrato_listar"))

        if request.method == "POST":
            opcao_contrato = dados_corretos.get("opcaoContrato")
            arquivoContrato = request.files.get("arquivoContrato")

            if contrato.arquivo_contrato_id:  
                if not opcao_contrato:
                    validacao_campos_obrigatorios["opcaoContrato"] = "Selecione uma opção"
                    gravar_banco = False
                elif opcao_contrato == "alterar":
                    if not arquivoContrato or not arquivoContrato.filename:
                        validacao_campos_obrigatorios["arquivoContrato"] = "Arquivo Contrato é obrigatório quando você escolhe enviar novo"
                        gravar_banco = False
            else:  
                if not arquivoContrato or not arquivoContrato.filename:
                    validacao_campos_obrigatorios["arquivoContrato"] = "Arquivo Contrato é obrigatório"
                    gravar_banco = False

            if arquivoContrato and arquivoContrato.filename:
                if arquivoContrato.mimetype not in ["application/pdf"]:
                    validacao_campos_erros["arquivoContrato"] = "O arquivo deve estar em formato PDF"
                    gravar_banco = False

            if not gravar_banco:
                flash(("Verifique os campos destacados em vermelho!", "warning"))
            else:
                if (not contrato.arquivo_contrato_id) or (opcao_contrato == "alterar"):
                    if arquivoContrato and arquivoContrato.filename:
                        arquivo = upload_arquivo(
                            arquivoContrato,
                            "UPLOAD_CONTRATO_ASSINADO",
                            f"arquivo_contrato-{contrato.cliente.identificacao}-{dataHoje}",
                        )
                        contrato.arquivo_contrato_id = arquivo.id
                contrato.contrato_assinado = True
                db.session.commit()
                flash(("Contrato Assinado cadastrado com sucesso!", "success"))
                return redirect(url_for("contrato_listar"))

    except Exception as e:
        flash(("Erro ao efetuar upload de arquivo! Entre em contato com o suporte", "warning"))
        print(e)
        return redirect(url_for("contrato_listar"))

    return render_template(
        "sistema_hash/financeiro/contrato/contrato_assinado_cadastrar.html",
        contrato=contrato,
        dados_corretos=dados_corretos,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
    )
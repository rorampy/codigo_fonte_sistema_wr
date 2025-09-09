from sistema import app, db, requires_roles, current_user
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from sistema.models_views.sistema_wr.gerenciar.clientes.cliente_model import ClienteModel
from sistema._utilitarios import *


@app.route("/gerenciar/cliente/cadastrar", methods=["GET", "POST"])
@login_required
@requires_roles
def cadastrar_cliente():
    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True
    
    if request.method == "POST":
        tipo_cadastro = request.form["tipoCadastro"]
        nome_completo = request.form["nomeCompleto"]
        razao_social = request.form["razaoSocial"]
        cpf = request.form["cpf"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        email_cliente = request.form["emailCliente"]
        
        telefone_whats = request.form.get("telefoneWhats", "0")
        possui_whats = True if telefone_whats == "1" else False
        
        rua_endereco = request.form["ruaEndereco"]
        numero_endereco = request.form["numeroEndereco"]
        bairro_endereco = request.form["bairroEndereco"]
        cep_endereco = request.form["cepEndereco"]
        cidade_endereco = request.form["cidadeEndereco"]
        estado_endereco = request.form["estadoEndereco"]
        pais_endereco = request.form["paisEndereco"]
        
        campos = {
            "telefone": ["Telefone", telefone],
            "emailCliente": ["Email", email_cliente]
        }
        
        if tipo_cadastro == "cpf":
            campos["nomeCompleto"] = ["Nome Completo", nome_completo]
            campos["cpf"] = ["CPF", cpf]
        
        if tipo_cadastro == "cnpj":
            campos["razaoSocial"] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]
        
        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)
        
        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))
        
        if email_cliente:
            verificacao_email = ValidaForms.validar_email(email_cliente)
            if not "validado" in verificacao_email:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_email)
        
        if tipo_cadastro == "cpf":
            verificacao_cpf = ValidaForms.validar_cpf(cpf)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)
            
            cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
            pesquisa_cpf_banco = ClienteModel.query.filter_by(
                numero_documento=cpf_tratado
            ).first()
            if pesquisa_cpf_banco:
                gravar_banco = False
                validacao_campos_erros["cpf"] = (
                    f"O CPF informado já existe no banco de dados!"
                )
        
        if tipo_cadastro == "cnpj":
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)
            
            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            pesquisa_cnpj_banco = ClienteModel.query.filter_by(
                numero_documento=cnpj_tratado
            ).first()
            if pesquisa_cnpj_banco:
                gravar_banco = False
                validacao_campos_erros["cnpj"] = (
                    f"O CNPJ informado já existe no banco de dados!"
                )
        
        if email_cliente:
            pesquisa_email_banco = ClienteModel.query.filter_by(
                email=email_cliente
            ).first()
            if pesquisa_email_banco:
                gravar_banco = False
                validacao_campos_erros["emailCliente"] = (
                    f"O email informado já existe no banco de dados!"
                )
        
        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            
            if tipo_cadastro == "cpf":
                tipo_cadastro = 1
                identificacao = nome_completo
                numero_documento = cpf_tratado
            
            if tipo_cadastro == "cnpj":
                tipo_cadastro = 0
                identificacao = razao_social
                numero_documento = cnpj_tratado
            
            cliente = ClienteModel(
                fatura_via_cpf=tipo_cadastro,
                identificacao=identificacao,
                numero_documento=numero_documento,
                email=email_cliente,
                telefone=telefone_tratado,
                possui_whats=possui_whats,
                endereco_rua=rua_endereco,
                endereco_numero=numero_endereco,
                endereco_bairro=bairro_endereco,
                endereco_cep=ValidaDocs.somente_numeros(cep_endereco),
                endereco_cidade=cidade_endereco,
                endereco_estado=estado_endereco,
                endereco_pais=pais_endereco if pais_endereco != '' else "Brasil", 
                ativo=True
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            flash(("Cliente cadastrado com sucesso!", "success"))
            return redirect(url_for("listar_clientes"))
    
    return render_template(
        "sistema_wr/gerenciar/clientes/cliente_cadastrar.html",
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=request.form,
    )

@app.route("/gerenciar/clientes", methods=["GET", "POST"])
@login_required
@requires_roles
def listar_clientes():
    if request.method == 'POST':
        celular = request.form.get('celular')
        celularFormatado = ValidaDocs.somente_numeros(celular)
        clientes = ClienteModel.filtrar_clientes(
            identficacao=request.form.get('identificacao'),
            celular=celularFormatado
        )
    else:
        clientes = ClienteModel.listar_clientes()
    return render_template("sistema_wr/gerenciar/clientes/cliente_listar.html", clientes=clientes, dados_corretos=request.form)


@app.route("/gerenciar/cliente/editar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def editar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
        return redirect(url_for("listar_clientes"))

    if cliente.ativo == 0:
        flash(("Este cliente não pode ser editado, pois está desativado!", "warning"))
        return redirect(url_for("listar_clientes"))
    
    dados_corretos = {
        "tipoCadastro": "cpf" if cliente.fatura_via_cpf == 1 else "cnpj",
        "razaoSocial": cliente.identificacao if cliente.fatura_via_cpf == 0 else "",
        "nomeCompleto": cliente.identificacao if cliente.fatura_via_cpf == 1 else "",
        "cpf": cliente.numero_documento if cliente.fatura_via_cpf == 1 else "",
        "cnpj": cliente.numero_documento if cliente.fatura_via_cpf == 0 else "",
        "telefone": cliente.telefone or "",
        "emailCliente": cliente.email or "",
        "telefoneWhats": "1" if cliente.possui_whats else "0",
        "ruaEndereco": cliente.endereco_rua or "",
        "numeroEndereco": cliente.endereco_numero or "",
        "bairroEndereco": cliente.endereco_bairro or "",
        "cepEndereco": cliente.endereco_cep or "",
        "cidadeEndereco": cliente.endereco_cidade or "",
        "estadoEndereco": cliente.endereco_estado or "",
        "paisEndereco": cliente.endereco_pais or ""
    }

    validacao_campos_obrigatorios = {}
    validacao_campos_erros = {}
    gravar_banco = True

    if request.method == "POST":
        tipo_cadastro = request.form["tipoCadastro"]
        nome_completo = request.form["nomeCompleto"]
        razao_social = request.form["razaoSocial"]
        cpf = request.form["cpf"]
        cnpj = request.form["cnpj"]
        telefone = request.form["telefone"]
        email_cliente = request.form["emailCliente"]
        
        telefone_whats = request.form.get("telefoneWhats", "0")
        possui_whats = True if telefone_whats == "1" else False
        
        rua_endereco = request.form["ruaEndereco"]
        numero_endereco = request.form["numeroEndereco"]
        bairro_endereco = request.form["bairroEndereco"]
        cep_endereco = request.form["cepEndereco"]
        cidade_endereco = request.form["cidadeEndereco"]
        estado_endereco = request.form["estadoEndereco"]
        pais_endereco = request.form["paisEndereco"]
        
        dados_corretos.update(request.form.to_dict())
        dados_corretos["telefoneWhats"] = telefone_whats
        
        campos = {
            "telefone": ["Telefone", telefone],
            "emailCliente": ["Email", email_cliente]
        }
        
        if tipo_cadastro == "cpf":
            campos["nomeCompleto"] = ["Nome Completo", nome_completo]
            campos["cpf"] = ["CPF", cpf]
        
        if tipo_cadastro == "cnpj":
            campos["razaoSocial"] = ["Razão Social", razao_social]
            campos["cnpj"] = ["CNPJ", cnpj]

        validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

        if not "validado" in validacao_campos_obrigatorios:
            gravar_banco = False
            flash((f"Verifique os campos destacados em vermelho!", "warning"))
        
        if email_cliente:
            verificacao_email = ValidaForms.validar_email(email_cliente)
            if not "validado" in verificacao_email:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_email)

        if tipo_cadastro == "cpf":
            verificacao_cpf = ValidaForms.validar_cpf(cpf)
            if not "validado" in verificacao_cpf:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cpf)

            cpf_tratado = ValidaDocs.remove_pontuacao_cpf(cpf)
            if cliente.numero_documento != cpf_tratado:
                pesquisa_cpf_banco = ClienteModel.query.filter_by(
                    numero_documento=cpf_tratado
                ).first()
                if pesquisa_cpf_banco:
                    gravar_banco = False
                    validacao_campos_erros["cpf"] = (
                        f"O CPF informado já existe no banco de dados!"
                    )

        if tipo_cadastro == "cnpj":
            verificacao_cnpj = ValidaForms.validar_cnpj(cnpj)
            if not "validado" in verificacao_cnpj:
                gravar_banco = False
                validacao_campos_erros.update(verificacao_cnpj)

            cnpj_tratado = ValidaDocs.remove_pontuacao_cnpj(cnpj)
            if cliente.numero_documento != cnpj_tratado:
                pesquisa_cnpj_banco = ClienteModel.query.filter_by(
                    numero_documento=cnpj_tratado
                ).first()
                if pesquisa_cnpj_banco:
                    gravar_banco = False
                    validacao_campos_erros["cnpj"] = (
                        f"O CNPJ informado já existe no banco de dados!"
                    )
        
        if email_cliente and cliente.email != email_cliente:
            pesquisa_email_banco = ClienteModel.query.filter_by(
                email=email_cliente
            ).first()
            if pesquisa_email_banco:
                gravar_banco = False
                validacao_campos_erros["emailCliente"] = (
                    f"O email informado já existe no banco de dados!"
                )

        if gravar_banco == True:
            telefone_tratado = Tels.remove_pontuacao_telefone_celular_br(telefone)
            
            if tipo_cadastro == "cpf":
                tipo_cadastro = 1
                identificacao = nome_completo
                numero_documento = cpf_tratado
            
            if tipo_cadastro == "cnpj":
                tipo_cadastro = 0
                identificacao = razao_social
                numero_documento = cnpj_tratado

            cliente.fatura_via_cpf = tipo_cadastro
            cliente.identificacao = identificacao
            cliente.numero_documento = numero_documento
            cliente.email = email_cliente
            cliente.telefone = telefone_tratado
            cliente.possui_whats = possui_whats
            cliente.endereco_rua = rua_endereco
            cliente.endereco_numero = numero_endereco
            cliente.endereco_bairro = bairro_endereco
            cliente.endereco_cep = ValidaDocs.somente_numeros(cep_endereco)
            cliente.endereco_cidade = cidade_endereco
            cliente.endereco_estado = estado_endereco
            cliente.endereco_pais = pais_endereco if pais_endereco != '' else "Brasil"
            cliente.ativo = True

            db.session.commit()

            flash(("Cliente editado com sucesso!", "success"))
            return redirect(url_for("listar_clientes"))

    return render_template(
        "sistema_wr/gerenciar/clientes/cliente_editar.html",
        cliente=cliente,
        campos_obrigatorios=validacao_campos_obrigatorios,
        campos_erros=validacao_campos_erros,
        dados_corretos=dados_corretos
    )

@app.route("/gerenciar/cliente/desativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def desativar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
    cliente.ativo = 0
    db.session.commit()
    flash(('Cliente desativado com sucesso!', 'success'))
    return redirect(url_for("listar_clientes"))


@app.route("/gerenciar/cliente/ativar/<int:id>", methods=["GET", "POST"])
@login_required
@requires_roles
def ativar_cliente(id):
    cliente = ClienteModel.obter_cliente_por_id(id)
    if cliente is None:
        flash(("Cliente não encontrado!", "warning"))
    cliente.ativo = 1
    db.session.commit()
    flash(('Cliente ativado com sucesso!', 'success'))
    return redirect(url_for("listar_clientes"))

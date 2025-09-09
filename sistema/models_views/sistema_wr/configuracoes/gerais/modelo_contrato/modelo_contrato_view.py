import os
from sistema import app, db, requires_roles
from logs_sistema import flask_logger
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sistema.models_views.sistema_wr.configuracoes.gerais.modelo_contrato.modelo_contrato_model import ModeloContratoModel
from sistema.models_views.sistema_wr.configuracoes.gerais.variaveis_contrato.variavel_modelo_contrato_model import VariavelModeloContrato
from sistema._utilitarios import *

@app.route('/configuracoes/modelos-contrato/listagem')
@requires_roles
@login_required
def listar_modelos_contratos():
    modelos = ModeloContratoModel.obter_modelos_contratos_ativos()
    return render_template(
        'sistema_wr/configuracao/gerais/modelo_contrato/listagem_modelo_contrato.html',
        modelos=modelos
    )


@app.route('/configuracoes/cadastrar-modelo-contrato', methods=['GET', 'POST'])
@requires_roles
@login_required
def cadastrar_modelo_contrato():
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        variaveis_modelo = VariavelModeloContrato.variaveis_modelo_contrato()

        if request.method == "POST":
            nomeModelo = request.form["nomeModelo"]
            conteudo = request.form["conteudo"]

            campos = {
                "nomeModelo": ["Nome do Modelo", nomeModelo],
                "conteudo": ["Conteúdo do Modelo", conteudo],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                modelo_contrato = ModeloContratoModel(
                    nome_modelo=nomeModelo,
                    conteudo=conteudo,
                    usuario_id=int(current_user.id),
                    ativo=True
                )

                db.session.add(modelo_contrato)
                db.session.commit()

                flash(("Modelo de contrato cadastrado com sucesso", "success"))
                return redirect(url_for("listar_modelos_contratos"))

        return render_template(
            'sistema_wr/configuracao/gerais/modelo_contrato/cadastrar_modelo_contrato.html',
            dados_corretos=request.form,
            campos_obrigatorios=validacao_campos_obrigatorios,
            campos_erros=validacao_campos_erros,
            variaveis_modelo=variaveis_modelo
        )

    except Exception as e:
        print("['ERRO] Erro ao tentar cadastrar novo modelo de contrato!: ", e)
        flash(('Houve um erro ao tentar cadastrar novo modelo de contrato! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('cadastrar_modelo_contrato'))
    
@app.route('/configuracoes/editar-modelo-contrato/<int:modelo_id>', methods=['GET', 'POST'])
@requires_roles
@login_required
def editar_modelo_contrato(modelo_id):
    try:
        validacao_campos_obrigatorios = {}
        validacao_campos_erros = {}
        gravar_banco = True

        variaveis_modelo = VariavelModeloContrato.variaveis_modelo_contrato()

        modelo = ModeloContratoModel.obter_modelo_contrato_ativo_por_id(modelo_id)
        if not modelo:
            flash(("Modelo de contrato não encontrado!", "error"))
            return redirect(url_for("listar_modelos_contratos"))

        if request.method == "POST":
            nomeModelo = request.form["nomeModelo"]
            conteudo = request.form["conteudo"]

            campos = {
                "nomeModelo": ["Nome do Modelo", nomeModelo],
                "conteudo": ["Conteúdo do Modelo", conteudo],
            }

            validacao_campos_obrigatorios = ValidaForms.campo_obrigatorio(campos)

            if not "validado" in validacao_campos_obrigatorios:
                gravar_banco = False
                flash((f"Verifique os campos destacados em vermelho!", "warning"))

            if gravar_banco:
                modelo.nome_modelo = nomeModelo
                modelo.conteudo = conteudo

                db.session.commit()

                flash(("Modelo de contrato atualizado com sucesso", "success"))
                return redirect(url_for("listar_modelos_contratos"))

        return render_template(
            'sistema_wr/configuracao/gerais/modelo_contrato/editar_modelo_contrato.html',
            modelo=modelo,
            dados_corretos=request.form,
            campos_obrigatorios=validacao_campos_obrigatorios,
            campos_erros=validacao_campos_erros,
            variaveis_modelo=variaveis_modelo
        )

    except Exception as e:
        print("['ERRO] Erro ao tentar editar modelo de contrato!: ", e)
        flash(('Houve um erro ao tentar editar modelo de contrato! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('listar_modelos_contratos'))
    

@app.route('/configuracoes/excluir-modelo-contrato/<int:modelo_id>', methods=['GET', 'POST'])
@requires_roles
@login_required
def excluir_modelo_contrato(modelo_id):
    try:
        modelo = ModeloContratoModel.obter_modelo_contrato_ativo_por_id(modelo_id)
        if not modelo:
            flash(("Modelo de contrato não encontrado!", "error"))
            return redirect(url_for("listar_modelos_contratos"))

        modelo.deletado = True
        modelo.ativo = False

        db.session.commit()

        flash(("Modelo de contrato excluído com sucesso", "success"))
        return redirect(url_for('listar_modelos_contratos'))
    except Exception as e:
        print("['ERRO] Erro ao tentar excluir modelo de contrato!: ", e)
        flash(('Houve um erro ao tentar excluir modelo de contrato! Entre em contato com o suporte.', 'warning'))
        return redirect(url_for('listar_modelos_contratos'))
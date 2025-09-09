from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.sistema_wr.parametrizacao.variavel_sistema_model import VariavelSistemaModel
from sistema._utilitarios import Tels


@app.context_processor
def get_variaveis():
    variaveis = VariavelSistemaModel.obter_variaveis_de_sistema_por_id()

    return {
        'variaveis': variaveis
        }
    
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = UsuarioModel.obter_usuario_por_email(email)

        if not usuario or not usuario.verificar_senha(senha):
            flash((f"Email e/ou Senha incorreto(s)!", "warning"))

        else:
            login_user(usuario)
            return redirect(url_for("principal"))

    return render_template("sistema_wr/autenticacao/login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    # Limpa todos os dados da sessão ao fazer logout
    session.clear()
    logout_user()

    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
@requires_roles
def principal():
    
    return render_template(
        "sistema_wr/estrutura/dashboard.html"
    )


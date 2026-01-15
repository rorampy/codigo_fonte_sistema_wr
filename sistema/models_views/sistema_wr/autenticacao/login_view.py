from sistema import app, requires_roles, db
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from sistema.models_views.sistema_wr.autenticacao.usuario_model import UsuarioModel
from sistema.models_views.sistema_wr.parametrizacao.variavel_sistema_model import VariavelSistemaModel
from sistema._utilitarios import Tels, DataHora
from datetime import date
from sqlalchemy import func


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
    # Importação dos models necessários para as métricas
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_model import AtividadeModel
    from sistema.models_views.sistema_wr.gerenciar.projetos.atividade_solicitacao_model import SolicitacaoAtividadeModel
    from sistema.models_views.sistema_wr.gerenciar.projetos.lancamento_horas_model import LancamentoHorasModel
    
    # Métricas padrão
    metricas = {
        'minhas_atividades': 0,
        'atividades_expirando': 0,
        'atividades_atrasadas': 0,
        'atividade_mais_atrasada': None,
        'proxima_expirar': None,
        'solicitacoes_analise': 0,
        'horas_mes': 0.0
    }
    
    # 1. Minhas Atividades (como desenvolvedor, não concluídas/canceladas)
    # situacao_id: 1=Não iniciada, 2=Em andamento, 5=Pausada (excluindo 3=Concluída, 4=Cancelada)
    minhas_atividades = AtividadeModel.query.filter(
        AtividadeModel.desenvolvedor_id == current_user.id,
        AtividadeModel.deletado == False,
        AtividadeModel.situacao_id.in_([1, 2, 6])  # Não concluídas/canceladas
    ).all()
    metricas['minhas_atividades'] = len(minhas_atividades)
    
    # 2. Atividades prestes a expirar (próximos 7 dias)
    hoje = date.today()
    data_limite = DataHora.adicionar_dias_em_data(hoje, 7)
    
    atividades_expirando = AtividadeModel.query.filter(
        AtividadeModel.desenvolvedor_id == current_user.id,
        AtividadeModel.deletado == False,
        AtividadeModel.situacao_id.in_([1, 2, 6]),
        AtividadeModel.data_prazo_conclusao != None,
        AtividadeModel.data_prazo_conclusao <= data_limite,
        AtividadeModel.data_prazo_conclusao >= hoje
    ).order_by(AtividadeModel.data_prazo_conclusao.asc()).all()
    metricas['atividades_expirando'] = len(atividades_expirando)
    
    # 3. Atividades atrasadas (já venceram)
    atividades_atrasadas = AtividadeModel.query.filter(
        AtividadeModel.desenvolvedor_id == current_user.id,
        AtividadeModel.deletado == False,
        AtividadeModel.situacao_id.in_([1, 2, 6]),
        AtividadeModel.data_prazo_conclusao != None,
        AtividadeModel.data_prazo_conclusao < hoje
    ).order_by(AtividadeModel.data_prazo_conclusao.asc()).all()
    metricas['atividades_atrasadas'] = len(atividades_atrasadas)
    
    # Atividade mais atrasada (a que venceu há mais tempo)
    if atividades_atrasadas:
        mais_atrasada = atividades_atrasadas[0]  # Já ordenado por data asc, então a primeira é a mais antiga
        dias_atraso = (hoje - mais_atrasada.data_prazo_conclusao).days
        metricas['atividade_mais_atrasada'] = {
            'id': mais_atrasada.id,
            'titulo': mais_atrasada.titulo[:35] + '...' if len(mais_atrasada.titulo) > 35 else mais_atrasada.titulo,
            'data': mais_atrasada.data_prazo_conclusao.strftime('%d/%m/%Y'),
            'dias_atraso': dias_atraso
        }
    
    # 4. Próxima a expirar (a mais próxima que ainda não venceu)
    proxima_expirar = AtividadeModel.query.filter(
        AtividadeModel.desenvolvedor_id == current_user.id,
        AtividadeModel.deletado == False,
        AtividadeModel.situacao_id.in_([1, 2, 6]),
        AtividadeModel.data_prazo_conclusao != None,
        AtividadeModel.data_prazo_conclusao >= hoje
    ).order_by(AtividadeModel.data_prazo_conclusao.asc()).first()
    
    if proxima_expirar:
        metricas['proxima_expirar'] = {
            'id': proxima_expirar.id,
            'titulo': proxima_expirar.titulo[:40] + '...' if len(proxima_expirar.titulo) > 40 else proxima_expirar.titulo,
            'data': proxima_expirar.data_prazo_conclusao.strftime('%d/%m/%Y'),
            'dias_restantes': (proxima_expirar.data_prazo_conclusao - hoje).days
        }
    
    # 5. Solicitações em análise (situacao_id = 7)
    solicitacoes_analise = SolicitacaoAtividadeModel.query.filter(
        SolicitacaoAtividadeModel.deletado == False,
        SolicitacaoAtividadeModel.situacao_id == 7  # Em Análise
    ).count()
    metricas['solicitacoes_analise'] = solicitacoes_analise
    
    # 6. Horas trabalhadas no mês atual
    primeiro_dia_mes = date(hoje.year, hoje.month, 1)
    
    horas_mes = db.session.query(func.sum(LancamentoHorasModel.horas_gastas)).filter(
        LancamentoHorasModel.usuario_id == current_user.id,
        LancamentoHorasModel.deletado == False,
        LancamentoHorasModel.data_lancamento >= primeiro_dia_mes,
        LancamentoHorasModel.data_lancamento <= hoje
    ).scalar() or 0.0
    metricas['horas_mes'] = round(horas_mes, 1)
    
    # 7. Horas trabalhadas hoje
    horas_hoje = db.session.query(func.sum(LancamentoHorasModel.horas_gastas)).filter(
        LancamentoHorasModel.usuario_id == current_user.id,
        LancamentoHorasModel.deletado == False,
        LancamentoHorasModel.data_lancamento == hoje
    ).scalar() or 0.0
    metricas['horas_hoje'] = round(horas_hoje, 1)

    
    return render_template(
        "sistema_wr/estrutura/dashboard.html",
        metricas=metricas
    )


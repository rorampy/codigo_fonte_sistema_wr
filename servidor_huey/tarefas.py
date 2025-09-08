import os
import smtplib
from logs_sistema import flask_logger
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from huey import SqliteHuey, crontab
from config import *

# obtendo o caminho relativo para o banco ficar ao lado de tarefas.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bd_tarefas.db')

# instância
huey = SqliteHuey(filename=DB_PATH)


@huey.task(retries=3, retry_delay=30)
def enviar_email_html(titulo, corpo, destinatario):
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORTA, timeout=10)
    
    # se quiser ativar o debug do smtplib
    # server.set_debuglevel(1)
    server.starttls()
    server.login(EMAIL_LOGIN, EMAIL_SENHA)
    email_msg = MIMEMultipart()
    email_msg['From'] = EMAIL_LOGIN
    email_msg['To'] = destinatario
    email_msg['Subject'] = titulo
    email_msg.attach(MIMEText(corpo, 'html'))    # 'plain' = tipo texto | 'html' = tipo HTML
    
    server.sendmail(email_msg['From'], email_msg['To'], email_msg.as_string())
    server.quit()
    flask_logger.info(f'E-mail enviado com sucesso para o destinatario {destinatario}')
    return True

@huey.periodic_task(crontab(minute=0, hour=0)) # Executa todos os dias as 00:00
def validar_vigencia_contratos():
    from datetime import date
    from sistema.models_views.sistema_wr.contrato.contrato_model import ContratoModel
    from sistema import db
    from sistema import app 
    with app.app_context():
        contratos = ContratoModel.listar_contratos_ativos()
        hoje = date.today()
        for contrato in contratos:
            for prod in contrato.contrato_produto:
                if prod.vigencia_fim and prod.vigencia_fim < hoje:
                    contrato.status_contrato = 2  # Inativo
                    db.session.commit()
                    flask_logger.info(f'Contrato {contrato.id} inativado por fim de vigência.')


@huey.periodic_task(crontab(minute=5, hour=0)) # Executa todos os dias às 00:05
def validar_vencimento_recebimentos():
    """
    Valida o status dos recebimentos de acordo com a data de vencimento.
    - Se o recebimento está ativo, não está pago (status_id diferente de 2) e a data de vencimento já passou, altera para status de 'Pagamento Atrasado' (status_id=6).
    - Se o recebimento está ativo, não está pago e a data de vencimento é hoje, altera para status de 'Aguardando Pagamento' (status_id=5).
    """
    from datetime import date
    from sistema.models_views.sistema_wr.financeiro.recebimento.recebimento_model import RecebimentoModel
    from sistema import db
    from sistema import app
    with app.app_context():
        hoje = date.today()
        recebimentos = RecebimentoModel.query.filter_by(ativo=True).all()
        for receb in recebimentos:
            if receb.status_id != 2:  # Não está pago
                if receb.data_vencimento < hoje:
                    receb.status_id = 6  # Pagamento Atrasado
                    db.session.commit()
                    flask_logger.info(f'Recebimento {receb.id} marcado como Pagamento Atrasado.')
                elif receb.data_vencimento == hoje:
                    receb.status_id = 5  # Aguardando Pagamento
                    db.session.commit()
                    flask_logger.info(f'Recebimento {receb.id} marcado como Aguardando Pagamento.')
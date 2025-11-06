import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def send_alert_email(recipient_email: str, subject: str, body: str):
    """
    Envia um e-mail de alerta simples usando a configuração SMTP.
    """
    if settings.debug and not settings.SMTP_USER:
        logger.info(f"ALERTA (DEBUG): E-mail para {recipient_email} - Assunto: {subject}\nCorpo:\n{body}")
        return
    
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject

        part1 = MIMEText(body, "plain")
        msg.attach(part1)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls() 
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, recipient_email, msg.as_string())
        
        logger.info(f"E-mail de alerta enviado com sucesso para {recipient_email} ({subject})")

    except Exception as e:
        logger.error(f"ERRO ao enviar e-mail de alerta para {recipient_email}: {e}", exc_info=True)


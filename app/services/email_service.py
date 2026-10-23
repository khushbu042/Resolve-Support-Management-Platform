import logging
import smtplib
from email.message import EmailMessage

import structlog

from app.core.settings import get_settings

settings = get_settings()

logger = structlog.get_logger(__name__)


SMTP_HOST = settings.smtp_host
SMTP_PORT = settings.smtp_port
SMTP_USER = settings.smtp_user
SMTP_PASSWORD = settings.smtp_password
SMTP_USE_TLS = settings.smtp_use_tls
SMTP_FROM = settings.smtp_from


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        raise RuntimeError("SMTP_HOST is not configured")

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        if SMTP_USER:
            smtp.login(SMTP_USER, SMTP_PASSWORD or "")
        smtp.send_message(message)

    logger.info("Sent email to %s subject=%s", to_email, subject)

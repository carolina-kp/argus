"""Minimal SMTP email sender (zero-cost: Gmail app password).

Resend or any SMTP relay is a drop-in swap via the smtp_* settings.
"""
import logging
import smtplib
from email.message import EmailMessage

from argus_core.config import settings

logger = logging.getLogger("argus.email")


class EmailNotConfigured(RuntimeError):
    """Raised when SMTP credentials or addresses are missing."""


def send_email(subject: str, body_markdown: str) -> None:
    """Send the daily brief to the configured recipient.

    Sends a plain-text part (the Markdown source) so it renders in any client.
    """
    if not (settings.smtp_user and settings.smtp_password and settings.brief_recipient):
        raise EmailNotConfigured(
            "set SMTP_USER, SMTP_PASSWORD and BRIEF_RECIPIENT to send briefs"
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.brief_from or settings.smtp_user
    msg["To"] = settings.brief_recipient
    msg.set_content(body_markdown)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    logger.info('{"email":"sent","to":"%s"}', settings.brief_recipient)

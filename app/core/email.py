"""
SMTP Email Utility

Responsibilities:
- Send transactional emails via SMTP
- Fail safely (no auth breakage)
- Config-driven (Gmail / Zoho switchable)

Rules:
- No auth logic
- No DB access
- No FastAPI dependencies
"""

import smtplib
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings


def send_email(
    *,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> None:
    """
    Send email via configured SMTP.
    Failures are logged but never raised.
    """
    if not settings.SMTP_HOST:
        # SMTP not configured — silently ignore
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    if text_body:
        msg.set_content(text_body)

    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
            )
            server.send_message(msg)
    except Exception as exc:
        # IMPORTANT: never break login flow
        print(f"[EMAIL ERROR] {exc}")

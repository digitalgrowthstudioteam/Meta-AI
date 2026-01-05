"""
SMTP Email Utility

Responsibilities:
- Send transactional emails via SMTP
- Fail safely (no auth breakage)
- Config-driven (Gmail / Zoho / SES)

Rules:
- No auth logic
- No DB access
- No FastAPI dependencies
"""

import smtplib
import ssl
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
    MUST NEVER raise.
    """

    # --------------------------------------------------
    # CONFIG VALIDATION (HARD STOP, SAFE)
    # --------------------------------------------------
    if not all(
        [
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_FROM_EMAIL,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
        ]
    ):
        print("[EMAIL] SMTP not fully configured — skipping send")
        return

    try:
        port = int(settings.SMTP_PORT)
    except Exception:
        print("[EMAIL] Invalid SMTP_PORT — skipping send")
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    if text_body:
        msg.set_content(text_body)

    msg.add_alternative(html_body, subtype="html")

    try:
        # --------------------------------------------------
        # SSL (465)
        # --------------------------------------------------
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                port,
                context=context,
            ) as server:
                server.login(
                    settings.SMTP_USER,
                    settings.SMTP_PASSWORD,
                )
                server.send_message(msg)

        # --------------------------------------------------
        # STARTTLS (587 / others)
        # --------------------------------------------------
        else:
            with smtplib.SMTP(
                settings.SMTP_HOST,
                port,
                timeout=10,
            ) as server:
                server.ehlo()
                server.starttls()
                server.login(
                    settings.SMTP_USER,
                    settings.SMTP_PASSWORD,
                )
                server.send_message(msg)

    except Exception as exc:
        # ABSOLUTE RULE: NEVER BREAK LOGIN FLOW
        print(f"[EMAIL ERROR] {exc}")
        return

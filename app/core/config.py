"""
Application configuration
(Environment-based + Admin-controlled globals)
🔒 SINGLE SOURCE OF TRUTH
"""

import os
from typing import Optional
from dotenv import load_dotenv

# 🔥 LOAD .env EXPLICITLY FROM PROJECT ROOT
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


class Settings:
    # =================================================
    # DATABASE
    # =================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    # =================================================
    # PUBLIC APP (MAGIC LINK, BRANDING)
    # =================================================
    PUBLIC_APP_URL: str = os.getenv(
        "PUBLIC_APP_URL",
        "https://meta-ai.digitalgrowthstudio.in",
    ).rstrip("/")

    DASHBOARD_TITLE: str = os.getenv(
        "DASHBOARD_TITLE",
        "Digital Growth Studio",
    )

    DASHBOARD_SUBTITLE: str = os.getenv(
        "DASHBOARD_SUBTITLE",
        "Meta Ads AI Platform",
    )

    DASHBOARD_LOGO_URL: Optional[str] = os.getenv("DASHBOARD_LOGO_URL")

    # =================================================
    # GLOBAL SYSTEM FLAGS
    # =================================================
    AI_GLOBALLY_ENABLED: bool = os.getenv("AI_GLOBALLY_ENABLED", "true").lower() == "true"
    META_SYNC_ENABLED: bool = os.getenv("META_SYNC_ENABLED", "true").lower() == "true"
    ADMIN_CHAT_ENABLED: bool = os.getenv("ADMIN_CHAT_ENABLED", "true").lower() == "true"

    # =================================================
    # META OAUTH
    # =================================================
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "")

    # =================================================
    # SMTP (🔥 HARD-BOUND, NO SILENT SKIP)
    # =================================================
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "smtp.gmail.com")

    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    SMTP_USER: Optional[str] = (
        os.getenv("SMTP_USER")
        or os.getenv("SMTP_USERNAME")
        or os.getenv("EMAIL_FROM")
        or os.getenv("EMAILS_FROM_EMAIL")
    )

    SMTP_PASSWORD: Optional[str] = (
        os.getenv("SMTP_PASSWORD")
        or os.getenv("SMTP_PASS")
        or os.getenv("GMAIL_APP_PASSWORD")
    )

    SMTP_FROM_EMAIL: Optional[str] = (
        os.getenv("SMTP_FROM_EMAIL")
        or os.getenv("EMAIL_FROM")
        or os.getenv("EMAILS_FROM_EMAIL")
    )

    # =================================================
    # SYSTEM
    # =================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    SYSTEM_READ_ONLY: bool = os.getenv("SYSTEM_READ_ONLY", "false").lower() == "true"


settings = Settings()

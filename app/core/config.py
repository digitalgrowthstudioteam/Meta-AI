"""
Application configuration
(Environment-based + Admin-controlled globals)
🔒 SINGLE SOURCE OF TRUTH
"""

import os
from typing import Optional


class Settings:
    # =================================================
    # DATABASE
    # =================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # =================================================
    # PUBLIC APP (MAGIC LINK, BRANDING)
    # =================================================
    PUBLIC_APP_URL: str = os.getenv(
        "PUBLIC_APP_URL",
        "https://meta-ai.digitalgrowthstudio.in",
    )

    DASHBOARD_TITLE: str = os.getenv(
        "DASHBOARD_TITLE",
        "Digital Growth Studio",
    )

    DASHBOARD_SUBTITLE: str = os.getenv(
        "DASHBOARD_SUBTITLE",
        "Meta Ads AI Platform",
    )

    DASHBOARD_LOGO_URL: Optional[str] = os.getenv(
        "DASHBOARD_LOGO_URL",
        None,
    )

    # =================================================
    # GLOBAL SYSTEM KILL SWITCHES (ADMIN POWER)
    # =================================================
    # 🔒 MASTER AI SWITCH
    AI_GLOBALLY_ENABLED: bool = os.getenv(
        "AI_GLOBALLY_ENABLED",
        "true",
    ).lower() == "true"

    # 🔒 META SYNC / OAUTH SWITCH
    META_SYNC_ENABLED: bool = os.getenv(
        "META_SYNC_ENABLED",
        "true",
    ).lower() == "true"

    # 🔒 ADMIN ↔ USER CHAT SYSTEM
    ADMIN_CHAT_ENABLED: bool = os.getenv(
        "ADMIN_CHAT_ENABLED",
        "true",
    ).lower() == "true"

    # =================================================
    # META OAUTH
    # =================================================
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "")

    # =================================================
    # SMTP (OPTIONAL)
    # =================================================
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")

    # =================================================
    # SYSTEM METADATA
    # =================================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    SYSTEM_READ_ONLY: bool = os.getenv(
        "SYSTEM_READ_ONLY",
        "false",
    ).lower() == "true"


settings = Settings()

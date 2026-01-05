"""
Application configuration
(Environment-based, safe defaults)
"""

import os
from typing import Optional


class Settings:
    # ======================
    # Database
    # ======================
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # ======================
    # Public App URL (CRITICAL FOR MAGIC LINK)
    # ======================
    # Used to build absolute URLs in emails
    # Fallback is safe for prod if env is missing
    PUBLIC_APP_URL: str = os.getenv(
        "PUBLIC_APP_URL",
        "https://meta-ai.digitalgrowthstudio.in",
    )

    # ======================
    # Meta OAuth
    # ======================
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    META_REDIRECT_URI: str = os.getenv("META_REDIRECT_URI", "")

    # ===============================
    # SMTP (OPTIONAL)
    # ===============================
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")


settings = Settings()

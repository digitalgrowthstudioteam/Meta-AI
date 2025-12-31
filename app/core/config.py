"""
Application configuration
(Environment-based, safe defaults)
"""

import os
from typing import Optional


class Settings:
    # ===============================
    # DATABASE
    # ===============================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://meta_ai_user:StrongPassword123@localhost:5432/meta_ai_db"
    )

    # ===============================
    # SMTP (OPTIONAL)
    # ===============================
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL: Optional[str] = os.getenv("SMTP_FROM_EMAIL")


settings = Settings()

"""
Application configuration
(Environment-based, safe defaults)
"""

import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://meta_ai_user:StrongPassword123@localhost:5432/meta_ai_db"
    )


settings = Settings()

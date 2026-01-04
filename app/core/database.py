"""
Database engine configuration (LAZY INIT)

IMPORTANT:
- Engine MUST NOT be created at import time
- This avoids crashes when DATABASE_URL is not yet loaded
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.core.base import Base


# =========================================================
# LAZY ENGINE (SAFE)
# =========================================================
_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """
    Lazily create and return the async engine.
    """
    global _engine

    if _engine is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
        )

    return _engine


# =========================================================
# METADATA ACCESS (FOR ALEMBIC / INSPECTION)
# =========================================================
metadata = Base.metadata

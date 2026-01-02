"""
Database engine configuration
"""

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.base import Base


# =========================================================
# ASYNC ENGINE
# =========================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


# =========================================================
# METADATA ACCESS (FOR ALEMBIC / INSPECTION ONLY)
# =========================================================
metadata = Base.metadata

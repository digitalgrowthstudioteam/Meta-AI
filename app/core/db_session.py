"""
Async database session setup
(No connection is made until used)
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings


# =========================================================
# ASYNC ENGINE
# =========================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


# =========================================================
# SESSION FACTORY
# =========================================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# =========================================================
# FASTAPI DEPENDENCY
# =========================================================
async def get_db():
    """
    FastAPI dependency that provides an async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session

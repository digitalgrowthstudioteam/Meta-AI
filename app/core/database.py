from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.base import Base  # ✅ SAFE IMPORT

DATABASE_URL = "postgresql+asyncpg://meta_ai_user:StrongPassword123@localhost:5432/meta_ai_db"

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 🔒 CRITICAL: load models AFTER Base is fully defined
import app.models  # DO NOT REMOVE

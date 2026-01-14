import sys
import os
import asyncio
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# =========================================================
# Ensure project root is on PYTHONPATH
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# =========================================================
# DATABASE URL (env-first, safe fallback)
# =========================================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://meta_ai_user:StrongNewPassword123!@127.0.0.1:5432/meta_ai_db",
)

# =========================================================
# Alembic Config
# =========================================================
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

# =========================================================
# Import ALL models via the central init file
# =========================================================
from app.core.database import Base

# This single line imports everything in the correct order (Payment -> Subscription -> User)
import app.models 

target_metadata = Base.metadata

# =========================================================
# OFFLINE MIGRATIONS
# =========================================================
def run_migrations_offline():
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# =========================================================
# ONLINE MIGRATIONS (ASYNC — FIXED)
# =========================================================
def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    asyncio.run(run_async_migrations())

# =========================================================
# ENTRYPOINT
# =========================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import sys
from pathlib import Path
import os
import asyncio
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
# Database URL (env-first, fallback safe)
# =========================================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://meta_ai_user:StrongNewPassword123!@127.0.0.1:5432/meta_ai_db",
)

# =========================================================
# Alembic config
# =========================================================
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

# =========================================================
# Import ONLY EXISTING MODELS
# =========================================================
from app.core.database import Base

import app.auth.models
import app.users.models
import app.plans.models
import app.plans.subscription_models
import app.meta_api.models
import app.campaigns.models
import app.meta_insights.models.campaign_daily_metrics
import app.meta_insights.models.campaign_breakdown_daily_metrics
import app.admin.models
import app.ai_engine.models.action_models

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
# ONLINE MIGRATIONS
# =========================================================
def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(
                lambda conn: context.configure(
                    connection=conn,
                    target_metadata=target_metadata,
                )
            )
            await connection.run_sync(context.run_migrations)
        await connectable.dispose()

    asyncio.run(run_async_migrations())

# =========================================================
# ENTRYPOINT
# =========================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

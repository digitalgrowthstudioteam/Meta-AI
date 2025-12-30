import sys
from pathlib import Path

# =========================================================
# Ensure project root is on PYTHONPATH for Alembic
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.database import Base

# =========================================================
# Import ALL models so Alembic can detect tables
# (NO database calls at import time)
# =========================================================
import app.users.models
import app.plans.models
import app.plans.subscription_models
import app.meta_api.models
import app.campaigns.models
import app.ai_engine.models.action_models
import app.audience_engine.models
import app.billing.payment_models
import app.billing.invoice_models

# =========================================================
# Alembic Config
# =========================================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATIONS
# =========================================================
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE MIGRATIONS (ASYNC, SQLALCHEMY 2.0 SAFE)
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

    import asyncio
    asyncio.run(run_async_migrations())


# =========================================================
# ENTRYPOINT
# =========================================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

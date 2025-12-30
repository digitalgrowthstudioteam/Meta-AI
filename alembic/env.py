import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.core.database import Base

# Import models so Alembic can see them (no DB calls)
import app.users.models
import app.plans.models
import app.plans.subscription_models
import app.meta_api.models
import app.campaigns.models
import app.ai_engine.models.action_models
import app.audience_engine.models
import app.billing.payment_models
import app.billing.invoice_models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


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


def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    asyncio.run(
        connectable.run_sync(do_run_migrations)
    )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

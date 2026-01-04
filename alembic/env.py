import os
import sys
from pathlib import Path
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# =========================================================
# Ensure project root is on PYTHONPATH
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# =========================================================
# DATABASE URL (ABSOLUTE SOURCE OF TRUTH)
# =========================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://meta_ai_user:StrongNewPassword123!@127.0.0.1:5432/meta_ai_db"

# =========================================================
# Alembic Config
# =========================================================
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# =========================================================
# Import Base FIRST
# =========================================================
from app.core.database import Base
target_metadata = Base.metadata

# =========================================================
# Import MODELS (NO DUPLICATES, NO DEAD MODULES)
# =========================================================
import app.auth.models
import app.users.models
import app.plans.models
import app.meta_api.models
import app.campaigns.models
import app.meta_insights.models.campaign_daily_metrics
import app.meta_insights.models.campaign_breakdown_daily_metrics
import app.ai_engine.models.action_models
import app.admin.models

# =========================================================
# OFFLINE MIGRATIONS
#

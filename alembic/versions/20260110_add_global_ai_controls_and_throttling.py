"""add global ai controls and throttling

Revision ID: 20260110_add_global_ai_controls_and_throttling
Revises: 20260106_fix_global_settings_schema
Create Date: 2026-01-10
"""

from alembic import op
import sqlalchemy as sa


# =========================
# ALEMBIC IDENTIFIERS
# =========================
revision = "20260110_add_global_ai_controls_and_throttling"
down_revision = "20260106_fix_global_settings_schema"
branch_labels = None
depends_on = None


# =========================
# UPGRADE
# =========================
def upgrade() -> None:
    with op.batch_alter_table("global_settings") as batch_op:
        # -----------------------------
        # PHASE P2 — GLOBAL AI TOGGLES
        # -----------------------------
        batch_op.add_column(
            sa.Column(
                "expansion_mode_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "fatigue_mode_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "auto_pause_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "confidence_gating_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )

        # -----------------------------
        # PHASE P2 — AI THROTTLING
        # -----------------------------
        batch_op.add_column(
            sa.Column(
                "max_optimizations_per_day",
                sa.Integer(),
                nullable=False,
                server_default="100",
            )
        )
        batch_op.add_column(
            sa.Column(
                "max_expansions_per_day",
                sa.Integer(),
                nullable=False,
                server_default="50",
            )
        )
        batch_op.add_column(
            sa.Column(
                "ai_refresh_frequency_minutes",
                sa.Integer(),
                nullable=False,
                server_default="60",
            )
        )


# =========================
# DOWNGRADE
# =========================
def downgrade() -> None:
    with op.batch_alter_table("global_settings") as batch_op:
        batch_op.drop_column("ai_refresh_frequency_minutes")
        batch_op.drop_column("max_expansions_per_day")
        batch_op.drop_column("max_optimizations_per_day")

        batch_op.drop_column("confidence_gating_enabled")
        batch_op.drop_column("auto_pause_enabled")
        batch_op.drop_column("fatigue_mode_enabled")
        batch_op.drop_column("expansion_mode_enabled")

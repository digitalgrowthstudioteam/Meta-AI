"""fix global_settings schema to match model

Revision ID: 20260106_fix_global_settings_schema
Revises: 85a724b0ebc0
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================
# ALEMBIC IDENTIFIERS
# =========================
revision = "20260106_fix_global_settings_schema"
down_revision = "85a724b0ebc0"
branch_labels = None
depends_on = None


# =========================
# UPGRADE
# =========================
def upgrade() -> None:
    # -------------------------------------------------
    # ADD MISSING COLUMNS (SAFE)
    # -------------------------------------------------
    with op.batch_alter_table("global_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "singleton_key",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.add_column(
            sa.Column(
                "site_name",
                sa.Text(),
                nullable=False,
                server_default="Digital Growth Studio",
            )
        )
        batch_op.add_column(
            sa.Column(
                "dashboard_title",
                sa.Text(),
                nullable=False,
                server_default="Meta Ads AI Platform",
            )
        )
        batch_op.add_column(
            sa.Column(
                "ai_globally_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            )
        )

        batch_op.create_unique_constraint(
            "uq_global_settings_singleton",
            ["singleton_key"],
        )

    # -------------------------------------------------
    # ENSURE SINGLE ROW EXISTS
    # -------------------------------------------------
    op.execute(
        """
        INSERT INTO global_settings (singleton_key)
        SELECT 1
        WHERE NOT EXISTS (SELECT 1 FROM global_settings);
        """
    )


# =========================
# DOWNGRADE
# =========================
def downgrade() -> None:
    with op.batch_alter_table("global_settings") as batch_op:
        batch_op.drop_constraint(
            "uq_global_settings_singleton",
            type_="unique",
        )
        batch_op.drop_column("updated_at")
        batch_op.drop_column("ai_globally_enabled")
        batch_op.drop_column("dashboard_title")
        batch_op.drop_column("site_name")
        batch_op.drop_column("singleton_key")

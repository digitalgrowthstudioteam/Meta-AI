"""admin safety & control layer

Revision ID: 20260106_admin_safety_layer
Revises: <PUT_YOUR_LAST_REVISION_ID_HERE>
Create Date: 2026-01-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================
# ALEMBIC IDENTIFIERS
# =========================
revision = "20260106_admin_safety_layer"
down_revision = None
branch_labels = None
depends_on = None


# =========================
# UPGRADE
# =========================
def upgrade() -> None:
    # -------------------------------------------------
    # PHASE 10 — CAMPAIGN ACTION LOGS (IMMUTABLE AUDIT)
    # -------------------------------------------------
    op.create_table(
        "campaign_action_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "actor_type",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "action_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "before_state",
            postgresql.JSONB,
            nullable=False,
        ),
        sa.Column(
            "after_state",
            postgresql.JSONB,
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.Text,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -------------------------------------------------
    # PHASE 14 — ADMIN OVERRIDES (ADD-ON / FORCE)
    # -------------------------------------------------
    op.create_table(
        "admin_overrides",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "extra_ai_campaigns",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "force_ai_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "override_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_admin_overrides_expiry",
        "admin_overrides",
        ["override_expires_at"],
    )

    # -------------------------------------------------
    # PHASE 14.4 — GLOBAL SETTINGS (KILL SWITCHES)
    # -------------------------------------------------
    op.create_table(
        "global_settings",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "maintenance_mode",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "meta_sync_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "ai_engine_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "site_title",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "logo_url",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # -------------------------------------------------
    # INSERT DEFAULT GLOBAL SETTINGS ROW (ID = 1)
    # -------------------------------------------------
    op.execute(
        """
        INSERT INTO global_settings (id, maintenance_mode, meta_sync_enabled, ai_engine_enabled)
        VALUES (1, false, true, true)
        """
    )


# =========================
# DOWNGRADE (SAFE REVERSAL)
# =========================
def downgrade() -> None:
    op.drop_table("global_settings")
    op.drop_table("admin_overrides")
    op.drop_table("campaign_action_logs")

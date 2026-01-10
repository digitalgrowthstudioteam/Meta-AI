"""create admin audit logs and rollback tokens

Revision ID: 20260110_create_admin_audit_logs
Revises: merge_plan_heads_20260109
Create Date: 2026-01-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================
# ALEMBIC IDENTIFIERS
# =========================
revision = "20260110_create_admin_audit_logs"
down_revision = "merge_plan_heads_20260109"
branch_labels = None
depends_on = None


# =========================
# UPGRADE
# =========================
def upgrade() -> None:
    # -------------------------------------------------
    # ADMIN AUDIT LOGS (IMMUTABLE)
    # -------------------------------------------------
    op.create_table(
        "admin_audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "admin_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_type",
            sa.String(length=64),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "action",
            sa.String(length=128),
            nullable=False,
            index=True,
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
            nullable=False,
        ),
        sa.Column(
            "rollback_token",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            unique=True,
            index=True,
        ),
        sa.Column(
            "ip_address",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
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


# =========================
# DOWNGRADE
# =========================
def downgrade() -> None:
    op.drop_table("admin_audit_logs")

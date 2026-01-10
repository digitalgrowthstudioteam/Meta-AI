"""create admin_pricing_configs

Revision ID: 20260110_0001
Revises: 20260109_merge_plan_heads
Create Date: 2026-01-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260110_0001"
down_revision = "20260109_merge_plan_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_pricing_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "plan_pricing",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "slot_packs",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=8),
            nullable=False,
            server_default="INR",
        ),
        sa.Column(
            "tax_percentage",
            sa.Integer(),
            nullable=False,
            server_default="18",
        ),
        sa.Column(
            "invoice_prefix",
            sa.String(length=32),
            nullable=False,
            server_default="DGS",
        ),
        sa.Column(
            "invoice_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "razorpay_mode",
            sa.String(length=16),
            nullable=False,
            server_default="live",
        ),
        sa.Column(
            "created_by_admin_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "version",
            name="uq_admin_pricing_version",
        ),
    )

    op.create_index(
        "ix_admin_pricing_configs_version",
        "admin_pricing_configs",
        ["version"],
    )

    op.create_index(
        "ix_admin_pricing_configs_is_active",
        "admin_pricing_configs",
        ["is_active"],
    )

    op.create_index(
        "ix_admin_pricing_configs_created_by_admin_id",
        "admin_pricing_configs",
        ["created_by_admin_id"],
    )


def downgrade():
    op.drop_index(
        "ix_admin_pricing_configs_created_by_admin_id",
        table_name="admin_pricing_configs",
    )
    op.drop_index(
        "ix_admin_pricing_configs_is_active",
        table_name="admin_pricing_configs",
    )
    op.drop_index(
        "ix_admin_pricing_configs_version",
        table_name="admin_pricing_configs",
    )
    op.drop_table("admin_pricing_configs")

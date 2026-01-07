"""
add unique active subscription per user constraint

Revision ID: 20260107_add_unique_active_subscription_index
Revises: 20260107_fix_missing_columns
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260107_add_unique_active_subscription_index"
down_revision = "20260107_fix_missing_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_active_subscription_per_user",
        "subscriptions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('trial', 'active')"),
    )


def downgrade():
    op.drop_index(
        "uq_active_subscription_per_user",
        table_name="subscriptions",
    )

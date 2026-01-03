"""add trial fields to subscriptions (manual)

Revision ID: 688791acd54f
Revises: 79356bb33da2
Create Date: 2026-01-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "688791acd54f"
down_revision = "79356bb33da2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "subscriptions",
        sa.Column("is_trial", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "subscriptions",
        sa.Column("trial_start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("trial_end_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("grace_ends_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("created_by_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "subscriptions",
        sa.Column("assigned_by_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("subscriptions", "assigned_by_admin")
    op.drop_column("subscriptions", "created_by_admin")
    op.drop_column("subscriptions", "grace_ends_at")
    op.drop_column("subscriptions", "trial_end_date")
    op.drop_column("subscriptions", "trial_start_date")
    op.drop_column("subscriptions", "is_trial")

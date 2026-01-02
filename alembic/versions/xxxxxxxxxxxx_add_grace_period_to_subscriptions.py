"""Add grace period support to subscriptions

Revision ID: add_grace_ends_at_to_subscriptions
Revises: 421f5e59c8d5
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_grace_ends_at_to_subscriptions'
down_revision = '421f5e59c8d5'
branch_labels = None
depends_on = None


def upgrade():
    # Add grace period end timestamp
    op.add_column(
        'subscriptions',
        sa.Column('grace_ends_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    # Remove grace period end timestamp
    op.drop_column('subscriptions', 'grace_ends_at')

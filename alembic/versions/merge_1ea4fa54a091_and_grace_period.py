"""Merge heads: meta oauth + grace period

Revision ID: merge_1ea4fa54a091_and_grace_period
Revises: 1ea4fa54a091, add_grace_ends_at_to_subscriptions
Create Date: 2026-01-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_1ea4fa54a091_and_grace_period'
down_revision = (
    '1ea4fa54a091',
    'add_grace_ends_at_to_subscriptions',
)
branch_labels = None
depends_on = None


def upgrade():
    # MERGE ONLY — NO SCHEMA CHANGES
    pass


def downgrade():
    # MERGE ONLY — NO SCHEMA CHANGES
    pass

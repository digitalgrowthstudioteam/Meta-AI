"""merge plan seeding heads

Revision ID: merge_plan_heads_20260109
Revises: add_plan_limits_and_seed, seed_plans_20260109
Create Date: 2026-01-09 13:30:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'merge_plan_heads_20260109'
down_revision = ('add_plan_limits_and_seed', 'seed_plans_20260109')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

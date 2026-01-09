"""add plan limits and seed initial plans

Revision ID: add_plan_limits_and_seed
Revises: df0b9dbf9711
Create Date: 2026-01-09 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_plan_limits_and_seed'
down_revision = 'df0b9dbf9711'
branch_labels = None
depends_on = None


def upgrade():
    # ======================================
    # PLANS — NEW ENFORCEMENT COLUMNS
    # ======================================

    # active ad account limit (NULL = unlimited)
    op.add_column(
        'plans',
        sa.Column('active_ad_account_limit', sa.Integer(), nullable=True)
    )

    # allows_addons (Agency only)
    op.add_column(
        'plans',
        sa.Column('allows_addons', sa.Boolean(), nullable=False, server_default='false')
    )

    # ======================================
    # SEED INITIAL PLANS (IDEMPOTENT)
    # ======================================

    op.execute("""
    INSERT INTO plans (
        name, price_monthly, ai_campaign_limit, active_ad_account_limit,
        allows_addons, is_trial_allowed, trial_days, is_active
    )
    VALUES
        ('trial',   0,    3, 1,  false, true,  7,  true),
        ('starter', 999,  3, 1,  false, false, NULL, true),
        ('pro',     1999, 20, 5, false, false, NULL, true),
        ('agency',  2999, 30, NULL, true, false, NULL, true)
    ON CONFLICT (name) DO NOTHING;
    """)


def downgrade():
    # ======================================
    # SCHEMA ROLLBACK (NO DATA ROLLBACK)
    # ======================================

    op.drop_column('plans', 'active_ad_account_limit')
    op.drop_column('plans', 'allows_addons')

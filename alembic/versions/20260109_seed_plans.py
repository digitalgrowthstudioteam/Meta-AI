"""seed initial plans

Revision ID: seed_plans_20260109
Revises: df0b9dbf9711
Create Date: 2026-01-09 12:45:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = 'seed_plans_20260109'
down_revision = 'df0b9dbf9711'
branch_labels = None
depends_on = None


def upgrade():
    # ======================================
    # SEED INITIAL PLANS (IDEMPOTENT)
    # ======================================
    op.execute("""
        INSERT INTO plans (
            name,
            price_monthly,
            monthly_price,
            ai_campaign_limit,
            max_ad_accounts,
            allows_addons,
            is_trial_allowed,
            trial_days,
            is_active
        )
        VALUES
            ('trial',   0,    0,    3, 1,  false, true,  7,  true),
            ('starter', 999,  999,  3, 1,  false, false, NULL, true),
            ('pro',     1999, 1999, 20, 5, false, false, NULL, true),
            ('agency',  2999, 2999, 30, NULL, true,  false, NULL, true)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade():
    # NOTE: We do not delete plans on downgrade
    pass

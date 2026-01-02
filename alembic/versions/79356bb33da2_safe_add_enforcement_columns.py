"""safe add enforcement columns

Revision ID: 79356bb33da2
Revises: 421f5e59c8d5
Create Date: 2025-12-30 17:20:48.619101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79356bb33da2'
down_revision = '421f5e59c8d5'
branch_labels = None
depends_on = None


def upgrade():
    # =========================
    # PLANS — ENFORCEMENT
    # =========================
    op.add_column(
        'plans',
        sa.Column('price_monthly', sa.Integer(), nullable=True)
    )
    op.add_column(
        'plans',
        sa.Column('ai_campaign_limit', sa.Integer(), nullable=True)
    )
    op.add_column(
        'plans',
        sa.Column('is_trial_allowed', sa.Boolean(), nullable=False)
    )
    op.add_column(
        'plans',
        sa.Column('trial_days', sa.Integer(), nullable=True)
    )
    op.add_column(
        'plans',
        sa.Column('is_active', sa.Boolean(), nullable=False)
    )

    # =========================
    # SUBSCRIPTIONS — ENFORCEMENT
    # =========================
    op.add_column(
        'subscriptions',
        sa.Column('status', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('starts_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'subscriptions',
        sa.Column('ends_at', sa.DateTime(), nullable=True)
    )

    # 🔐 Snapshot of AI limit at assignment time
    op.add_column(
        'subscriptions',
        sa.Column('ai_campaign_limit_snapshot', sa.Integer(), nullable=True)
    )

    # 🔐 Admin-assigned vs system-assigned
    op.add_column(
        'subscriptions',
        sa.Column('created_by_admin', sa.Boolean(), nullable=False)
    )

    # =========================
    # SUBSCRIPTIONS — GRACE PERIOD (PHASE 6.2)
    # =========================
    op.add_column(
        'subscriptions',
        sa.Column('grace_ends_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    # =========================
    # SUBSCRIPTIONS — GRACE PERIOD
    # =========================
    op.drop_column('subscriptions', 'grace_ends_at')

    # =========================
    # SUBSCRIPTIONS — ENFORCEMENT
    # =========================
    op.drop_column('subscriptions', 'created_by_admin')
    op.drop_column('subscriptions', 'ai_campaign_limit_snapshot')
    op.drop_column('subscriptions', 'ends_at')
    op.drop_column('subscriptions', 'starts_at')
    op.drop_column('subscriptions', 'status')

    # =========================
    # PLANS — ENFORCEMENT
    # =========================
    op.drop_column('plans', 'is_active')
    op.drop_column('plans', 'trial_days')
    op.drop_column('plans', 'is_trial_allowed')
    op.drop_column('plans', 'ai_campaign_limit')
    op.drop_column('plans', 'price_monthly')

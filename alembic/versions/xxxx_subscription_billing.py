"""create subscription_billing table

Revision ID: 20260120_subscription_billing
Revises: <PUT_PREVIOUS_REVISION_ID_HERE>
Create Date: 2026-01-20 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20260120_subscription_billing'
down_revision = '<PUT_PREVIOUS_REVISION_ID_HERE>'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'subscription_billing',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('plans.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('razorpay_subscription_id', sa.String(), nullable=True),
        sa.Column('razorpay_customer_id', sa.String(), nullable=True),
        sa.Column('billing_cycle', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=False),
        sa.Column('next_charge_at', sa.DateTime(), nullable=True),
        sa.Column('grace_end_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_index(
        'ix_subscription_billing_user',
        'subscription_billing',
        ['user_id']
    )

    op.create_index(
        'ix_subscription_billing_razorpay_sub',
        'subscription_billing',
        ['razorpay_subscription_id']
    )


def downgrade():
    op.drop_index('ix_subscription_billing_razorpay_sub', table_name='subscription_billing')
    op.drop_index('ix_subscription_billing_user', table_name='subscription_billing')
    op.drop_table('subscription_billing')

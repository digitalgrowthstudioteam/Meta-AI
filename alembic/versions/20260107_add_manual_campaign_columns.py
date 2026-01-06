"""add manual campaign columns

Revision ID: 20260107_manual_campaigns
Revises: da2b1043183e
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260107_manual_campaigns"
down_revision = "da2b1043183e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "campaigns",
        sa.Column("manual_purchased_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("manual_valid_from", sa.Date(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("manual_valid_till", sa.Date(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("manual_purchase_plan", sa.String(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("manual_price_paid", sa.Integer(), nullable=True),
    )
    op.add_column(
        "campaigns",
        sa.Column("manual_status", sa.String(), nullable=True),
    )


def downgrade():
    op.drop_column("campaigns", "manual_status")
    op.drop_column("campaigns", "manual_price_paid")
    op.drop_column("campaigns", "manual_purchase_plan")
    op.drop_column("campaigns", "manual_valid_till")
    op.drop_column("campaigns", "manual_valid_from")
    op.drop_column("campaigns", "manual_purchased_at")

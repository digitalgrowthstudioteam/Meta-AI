"""fix missing campaign + ad account columns

Revision ID: 20260107_fix_missing_columns
Revises: 20260107_manual_campaigns
Create Date: 2026-01-07
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260107_fix_missing_columns"
down_revision = "20260107_manual_campaigns"
branch_labels = None
depends_on = None


def upgrade():
    # ================================
    # campaigns table (MANUAL FIELDS)
    # ================================
    with op.batch_alter_table("campaigns") as batch:
        batch.add_column(
            sa.Column("manual_purchased_at", sa.DateTime(), nullable=True)
        )
        batch.add_column(
            sa.Column("manual_valid_from", sa.Date(), nullable=True)
        )
        batch.add_column(
            sa.Column("manual_valid_till", sa.Date(), nullable=True)
        )
        batch.add_column(
            sa.Column("manual_purchase_plan", sa.String(), nullable=True)
        )
        batch.add_column(
            sa.Column("manual_price_paid", sa.Integer(), nullable=True)
        )
        batch.add_column(
            sa.Column("manual_status", sa.String(), nullable=True)
        )

    # ================================
    # meta_ad_accounts table
    # ================================
    with op.batch_alter_table("meta_ad_accounts") as batch:
        batch.add_column(
            sa.Column("business_category", sa.String(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("campaigns") as batch:
        batch.drop_column("manual_purchased_at")
        batch.drop_column("manual_valid_from")
        batch.drop_column("manual_valid_till")
        batch.drop_column("manual_purchase_plan")
        batch.drop_column("manual_price_paid")
        batch.drop_column("manual_status")

    with op.batch_alter_table("meta_ad_accounts") as batch:
        batch.drop_column("business_category")

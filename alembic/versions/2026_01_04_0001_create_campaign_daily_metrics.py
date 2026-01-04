"""create campaign_daily_metrics

Revision ID: 0001_campaign_daily_metrics
Revises: 421f5e59c8d5
Create Date: 2026-01-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_campaign_daily_metrics"
down_revision = "421f5e59c8d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_daily_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),

        # core performance metrics
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("purchases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False, server_default="0"),

        # derived KPIs (stored, not computed at query time)
        sa.Column("ctr", sa.Numeric(6, 4), nullable=True),
        sa.Column("cpl", sa.Numeric(12, 2), nullable=True),
        sa.Column("cpa", sa.Numeric(12, 2), nullable=True),
        sa.Column("roas", sa.Numeric(8, 4), nullable=True),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # unique constraint: one row per campaign per day
    op.create_unique_constraint(
        "uq_campaign_date",
        "campaign_daily_metrics",
        ["campaign_id", "date"],
    )

    # indexes for AI + reporting
    op.create_index(
        "ix_campaign_daily_metrics_campaign_id",
        "campaign_daily_metrics",
        ["campaign_id"],
    )
    op.create_index(
        "ix_campaign_daily_metrics_date",
        "campaign_daily_metrics",
        ["date"],
    )


def downgrade() -> None:
    op.drop_index("ix_campaign_daily_metrics_date", table_name="campaign_daily_metrics")
    op.drop_index(
        "ix_campaign_daily_metrics_campaign_id",
        table_name="campaign_daily_metrics",
    )
    op.drop_constraint(
        "uq_campaign_date",
        "campaign_daily_metrics",
        type_="unique",
    )
    op.drop_table("campaign_daily_metrics")

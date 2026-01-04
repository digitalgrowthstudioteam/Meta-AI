"""
create campaign_breakdown_aggregates

Revision ID: 0002_campaign_breakdown_aggregates
Revises: 0001_campaign_daily_metrics
Create Date: 2026-01-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0002_campaign_breakdown_aggregates"
down_revision = "0001_campaign_daily_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_breakdown_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # windowing
        sa.Column("window_type", sa.String(), nullable=False),
        sa.Column("window_start_date", sa.Date(), nullable=True),
        sa.Column("window_end_date", sa.Date(), nullable=False),

        # breakdown dimensions (nullable by design)
        sa.Column("creative_id", sa.String(), nullable=True),
        sa.Column("placement", sa.String(), nullable=True),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("gender", sa.String(), nullable=True),
        sa.Column("age_group", sa.String(), nullable=True),

        # metrics
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Numeric(14, 2), nullable=False, server_default="0"),

        # derived
        sa.Column("ctr", sa.Numeric(6, 3), nullable=True),
        sa.Column("cpl", sa.Numeric(10, 2), nullable=True),
        sa.Column("cpa", sa.Numeric(10, 2), nullable=True),
        sa.Column("roas", sa.Numeric(6, 2), nullable=True),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_cb_agg_campaign_window",
        "campaign_breakdown_aggregates",
        ["campaign_id", "window_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cb_agg_campaign_window",
        table_name="campaign_breakdown_aggregates",
    )
    op.drop_table("campaign_breakdown_aggregates")

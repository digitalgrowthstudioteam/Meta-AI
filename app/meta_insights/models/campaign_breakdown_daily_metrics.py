from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class CampaignBreakdownDailyMetrics(Base):
    """
    DAILY performance snapshot for campaign breakdowns.

    One row represents:
    - One campaign
    - One day
    - One breakdown combination (creative / placement / demo / geo)

    This table powers:
    - Best creative detection
    - Best placement detection
    - Geo & demographic insights
    - Materialized aggregation windows
    """

    __tablename__ = "campaign_breakdown_daily_metrics"

    # =========================
    # PRIMARY IDENTITY
    # =========================
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    metric_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # =========================
    # BREAKDOWN DIMENSIONS
    # (NULLABLE BY DESIGN)
    # =========================
    ad_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Meta Ad ID (creative-level breakdown)",
    )

    creative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Meta Creative ID (if available)",
    )

    platform: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="facebook / instagram / audience_network",
    )

    placement: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="feed / stories / reels / etc.",
    )

    age_group: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="18-24, 25-34, etc.",
    )

    gender: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="male / female / unknown",
    )

    region: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="City or region name",
    )

    # =========================
    # METRICS
    # =========================
    impressions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    clicks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    spend: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0.00,
    )

    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Leads or purchases",
    )

    conversion_value: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    ctr: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
    )

    cpl: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    cpa: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    roas: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )

    # =========================
    # META CONTEXT
    # =========================
    objective_type: Mapped[str] = mapped_column(
        nullable=False,
        doc="LEAD or SALES",
    )

    meta_account_id: Mapped[str] = mapped_column(
        nullable=False,
        doc="Meta Ad Account ID",
    )

    # =========================
    # AUDIT
    # =========================
    meta_fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================
# IDEMPOTENCY & PERFORMANCE
# =========================

Index(
    "ux_campaign_breakdown_daily_unique",
    CampaignBreakdownDailyMetrics.campaign_id,
    CampaignBreakdownDailyMetrics.metric_date,
    CampaignBreakdownDailyMetrics.ad_id,
    CampaignBreakdownDailyMetrics.platform,
    CampaignBreakdownDailyMetrics.placement,
    CampaignBreakdownDailyMetrics.age_group,
    CampaignBreakdownDailyMetrics.gender,
    CampaignBreakdownDailyMetrics.region,
    unique=True,
)

Index(
    "ix_campaign_breakdown_campaign_date",
    CampaignBreakdownDailyMetrics.campaign_id,
    CampaignBreakdownDailyMetrics.metric_date,
)

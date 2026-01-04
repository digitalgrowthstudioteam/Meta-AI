from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


# ============================================================
# CAMPAIGN-LEVEL AGGREGATES (WINDOWED INTELLIGENCE)
# ============================================================

class CampaignMetricsAggregate(Base):
    """
    AI-ready aggregated performance per campaign per time window.

    One row = one campaign × one window
    """

    __tablename__ = "campaign_metrics_aggregates"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    window_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="1d, 3d, 7d, 14d, 30d, 90d, lifetime",
    )

    window_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    window_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on which this aggregation was computed",
    )

    # -------------------------
    # AGGREGATED METRICS
    # -------------------------
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
        Numeric(14, 2),
        nullable=False,
        default=0.00,
    )

    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    revenue: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    # -------------------------
    # DERIVED METRICS
    # -------------------------
    ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    cpl: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    cpa: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    # -------------------------
    # AI SUPPORT
    # -------------------------
    days_covered: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_complete_window: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    data_quality_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Future AI confidence weighting",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


Index(
    "ux_campaign_metrics_aggregate_unique",
    CampaignMetricsAggregate.campaign_id,
    CampaignMetricsAggregate.window_type,
    unique=True,
)


# ============================================================
# BREAKDOWN-LEVEL AGGREGATES (WHAT WORKS INSIDE CAMPAIGN)
# ============================================================

class CampaignBreakdownAggregate(Base):
    """
    Aggregated performance broken down by creative, placement,
    geography, demographics, and device.

    One row = one campaign × one window × one breakdown slice
    """

    __tablename__ = "campaign_breakdown_aggregates"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    window_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    window_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    window_end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # -------------------------
    # BREAKDOWN DIMENSIONS
    # -------------------------
    creative_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    placement: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    gender: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    age_range: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="e.g. 18-24, 25-34",
    )

    device: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # -------------------------
    # METRICS
    # -------------------------
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
        Numeric(14, 2),
        nullable=False,
        default=0.00,
    )

    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    revenue: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    cpl: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    cpa: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


Index(
    "ix_campaign_breakdown_lookup",
    CampaignBreakdownAggregate.campaign_id,
    CampaignBreakdownAggregate.window_type,
    CampaignBreakdownAggregate.creative_id,
    CampaignBreakdownAggregate.placement,
    CampaignBreakdownAggregate.city,
    CampaignBreakdownAggregate.gender,
    CampaignBreakdownAggregate.age_range,
)

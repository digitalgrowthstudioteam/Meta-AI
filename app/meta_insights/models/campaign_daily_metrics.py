from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class CampaignDailyMetrics(Base):
    """
    RAW daily performance snapshot for a Meta campaign.

    This table is the SINGLE SOURCE OF TRUTH for:
    - Historical performance
    - Aggregation windows (1D, 3D, 7D, 30D, Lifetime)
    - AI explainability
    - Confidence & trend analysis

    One row = one campaign × one calendar date
    """

    __tablename__ = "campaign_daily_metrics"

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
        doc="Internal campaign ID (not Meta ID)",
    )

    metric_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date for which Meta reported performance (UTC)",
    )

    # =========================
    # DELIVERY METRICS
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
        doc="Amount spent in account currency",
    )

    # =========================
    # CONVERSION METRICS
    # =========================
    conversions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Leads or purchases depending on objective",
    )

    conversion_value: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
        doc="Revenue value (mainly for Sales campaigns)",
    )

    # =========================
    # DERIVED METRICS (AS REPORTED)
    # =========================
    ctr: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
        doc="Click-through rate (%)",
    )

    cpl: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Cost per lead (Lead campaigns)",
    )

    cpa: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Cost per acquisition (Sales campaigns)",
    )

    roas: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        doc="Return on ad spend (Sales campaigns)",
    )

    # =========================
    # META CONTEXT
    # =========================
    objective_type: Mapped[str] = mapped_column(
        nullable=False,
        doc="LEAD or SALES (copied from campaign at ingest time)",
    )

    meta_account_id: Mapped[str] = mapped_column(
        nullable=False,
        doc="Meta Ad Account ID (string, for traceability)",
    )

    # =========================
    # INGESTION & AUDIT
    # =========================
    meta_fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        doc="When this metric row was fetched from Meta",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================
# CONSTRAINTS & INDEXES
# =========================

# Ensure idempotency: one row per campaign per day
Index(
    "ux_campaign_daily_metrics_unique",
    CampaignDailyMetrics.campaign_id,
    CampaignDailyMetrics.metric_date,
    unique=True,
)

# Fast window aggregations
Index(
    "ix_campaign_daily_metrics_date",
    CampaignDailyMetrics.metric_date,
)

Index(
    "ix_campaign_daily_metrics_campaign_date",
    CampaignDailyMetrics.campaign_id,
    CampaignDailyMetrics.metric_date,
)

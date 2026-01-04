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
    PHASE 6.5 — RAW META CAMPAIGN DAILY METRICS

    Single source of truth for:
    - AI reads
    - Aggregations
    - Explainability
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
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # =========================
    # CORE METRICS
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
        default=0.0,
    )

    leads: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    purchases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    revenue: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0.0,
    )

    # =========================
    # DERIVED METRICS
    # =========================
    ctr: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
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
        Numeric(8, 4),
        nullable=True,
    )

    # =========================
    # AUDIT
    # =========================
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


# =========================
# CONSTRAINTS & INDEXES
# =========================
Index(
    "uq_campaign_date",
    CampaignDailyMetrics.campaign_id,
    CampaignDailyMetrics.date,
    unique=True,
)

Index(
    "ix_campaign_daily_metrics_campaign_id",
    CampaignDailyMetrics.campaign_id,
)

Index(
    "ix_campaign_daily_metrics_date",
    CampaignDailyMetrics.date,
)

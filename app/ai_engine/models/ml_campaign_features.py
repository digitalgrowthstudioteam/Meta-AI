from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


# =========================================================
# ML CAMPAIGN FEATURE STORE
# =========================================================
class MLCampaignFeature(Base):
    """
    Machine Learning feature store for campaign-level learning.

    One row = one campaign × one window × one snapshot date

    This table is used for:
    - ML model training
    - Offline evaluation
    - Category-level aggregation
    - Explainable predictions
    """

    __tablename__ = "ml_campaign_features"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    window_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="7d | 30d | 90d | lifetime",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Snapshot date for feature computation",
    )

    # -------------------------
    # PERFORMANCE FEATURES
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
        default=0.0,
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
    # TREND FEATURES (SHORT VS LONG)
    # -------------------------
    ctr_trend: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
        doc="CTR ratio vs longer baseline",
    )

    cpl_trend: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
        doc="CPL ratio vs longer baseline",
    )

    roas_trend: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
        doc="ROAS ratio vs longer baseline",
    )

    # -------------------------
    # HEALTH SIGNALS (RULE-ALIGNED)
    # -------------------------
    fatigue_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    decay_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    scale_flag: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # -------------------------
    # CONTEXT FEATURES
    # -------------------------
    objective_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    campaign_age_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Days since campaign creation",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Prevent duplicate snapshots
Index(
    "ux_ml_campaign_features_unique",
    MLCampaignFeature.campaign_id,
    MLCampaignFeature.window_type,
    MLCampaignFeature.as_of_date,
    unique=True,
)

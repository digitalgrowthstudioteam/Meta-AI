from sqlalchemy import (
    String,
    Integer,
    Numeric,
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
# ML BREAKDOWN FEATURE STORE
# =========================================================
class MLBreakdownFeature(Base):
    """
    Machine Learning feature store for breakdown-level learning.

    One row = one campaign × one breakdown slice × one window × snapshot

    Used for:
    - Creative performance learning
    - Audience & geo learning
    - Placement & device optimization
    - Global category strategy intelligence
    """

    __tablename__ = "ml_breakdown_features"

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
    )

    device: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
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
    # RANKING CONTEXT
    # -------------------------
    rank_within_campaign: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Rank of this breakdown slice within campaign",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Prevent duplicate snapshots per slice
Index(
    "ux_ml_breakdown_features_unique",
    MLBreakdownFeature.campaign_id,
    MLBreakdownFeature.window_type,
    MLBreakdownFeature.as_of_date,
    MLBreakdownFeature.creative_id,
    MLBreakdownFeature.placement,
    MLBreakdownFeature.city,
    MLBreakdownFeature.gender,
    MLBreakdownFeature.age_range,
    MLBreakdownFeature.device,
    unique=True,
)

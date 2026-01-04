from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


# =========================================================
# GLOBAL CATEGORY BREAKDOWN STATS (CROSS-USER LEARNING)
# =========================================================
class MLCategoryBreakdownStat(Base):
    """
    Stores global, anonymized performance intelligence
    aggregated across all users and campaigns.

    One row =
    business_category × breakdown slice × time window

    Used for:
    - Industry benchmarks
    - Strategy recommendations
    - Category-level ML learning
    """

    __tablename__ = "ml_category_breakdown_stats"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    business_category: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        doc="Resolved business category (high-confidence only)",
    )

    window_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="30d | 90d | lifetime",
    )

    # -------------------------
    # BREAKDOWN DIMENSIONS
    # -------------------------
    age_range: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    gender: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    placement: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    device: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # -------------------------
    # AGGREGATED METRICS
    # -------------------------
    avg_ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    avg_cpl: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    avg_cpa: Mapped[float | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    avg_roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    median_roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    # -------------------------
    # LEARNING CONFIDENCE
    # -------------------------
    sample_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of campaigns contributing to this stat",
    )

    confidence_score: Mapped[float] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        doc="Confidence based on sample size & variance (0–1)",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Prevent duplicate category slices
Index(
    "ux_ml_category_breakdown_stats_unique",
    MLCategoryBreakdownStat.business_category,
    MLCategoryBreakdownStat.window_type,
    MLCategoryBreakdownStat.age_range,
    MLCategoryBreakdownStat.gender,
    MLCategoryBreakdownStat.city,
    MLCategoryBreakdownStat.placement,
    MLCategoryBreakdownStat.device,
    unique=True,
)
`

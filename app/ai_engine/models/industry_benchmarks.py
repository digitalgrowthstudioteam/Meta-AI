"""
Industry / Category Benchmarks Model

PHASE 9.4 — FOUNDATION (LOCKED)

Purpose:
- Store industry-level performance benchmarks
- Computed from aggregated campaign data
- Read-only intelligence for AI comparison
- NO decisions
- NO Meta interaction
"""

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class IndustryBenchmark(Base):
    """
    One row represents:
    - One category
    - One objective (LEAD / SALES)
    - One time window (1d / 3d / 7d / 14d / 30d / 90d / lifetime)
    """

    __tablename__ = "industry_benchmarks"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    category: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        doc="Normalized campaign category (e.g. ecommerce, education, finance)",
    )

    objective_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        doc="LEAD or SALES",
    )

    window_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        doc="1d, 3d, 7d, 14d, 30d, 90d, lifetime",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date on which benchmark was computed",
    )

    # -------------------------
    # BENCHMARK METRICS (AVG)
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

    # -------------------------
    # DISTRIBUTION (AI SIGNALS)
    # -------------------------
    p25_ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    p50_ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    p75_ctr: Mapped[float | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    p25_roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    p50_roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    p75_roas: Mapped[float | None] = mapped_column(
        Numeric(8, 3),
        nullable=True,
    )

    # -------------------------
    # SAMPLE SIZE & QUALITY
    # -------------------------
    campaign_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of campaigns used to compute this benchmark",
    )

    data_quality_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Confidence weighting for AI (future Phase 9.5)",
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
        onupdate=datetime.utcnow,
        nullable=False,
    )


# --------------------------------------------------
# UNIQUENESS & LOOKUP PERFORMANCE
# --------------------------------------------------
Index(
    "ux_industry_benchmark_unique",
    IndustryBenchmark.category,
    IndustryBenchmark.objective_type,
    IndustryBenchmark.window_type,
    IndustryBenchmark.as_of_date,
    unique=True,
)

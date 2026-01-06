from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Float,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class AudienceInsight(Base):
    """
    Phase 20 — Audience Intelligence

    Stores explainable audience decisions:
    - KEEP / PAUSE / EXPAND
    - Backed by fatigue + performance signals
    """

    __tablename__ = "audience_insights"

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

    # -------------------------------------------------
    # DECISION
    # -------------------------------------------------
    suggestion_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="KEEP | PAUSE | EXPAND",
    )

    reason: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Human-readable explanation",
    )

    confidence_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="0–100 confidence",
    )

    # -------------------------------------------------
    # FATIGUE SIGNALS
    # -------------------------------------------------
    fatigue_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="0.0–1.0 (higher = more fatigue)",
    )

    frequency: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    ctr_trend: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        doc="Negative indicates decay",
    )

    cpm_trend: Mapped[float] = mapped_column(
        Float,
        nullable=True,
        doc="Positive indicates rising cost",
    )

    # -------------------------------------------------
    # EXPANSION SIGNALS
    # -------------------------------------------------
    conversion_lift: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Expected lift if expanded",
    )

    audience_size_delta: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Projected reach increase",
    )

    similar_audience_source: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="lookalike | interest | broad",
    )

    # -------------------------------------------------
    # META
    # -------------------------------------------------
    source: Mapped[str] = mapped_column(
        String,
        default="ai",
        nullable=False,
        doc="ai | rule | hybrid",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =====================================================
# INDEXES
# =====================================================
Index("ix_audience_insight_campaign_time", AudienceInsight.campaign_id, AudienceInsight.created_at)
Index("ix_audience_insight_type", AudienceInsight.suggestion_type)

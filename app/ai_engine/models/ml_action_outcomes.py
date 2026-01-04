from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid
import enum

from app.core.database import Base


# =========================================================
# ACTION OUTCOME ENUMS
# =========================================================
class ActionOutcomeLabel(str, enum.Enum):
    IMPROVED = "improved"
    NEUTRAL = "neutral"
    WORSENED = "worsened"
    UNKNOWN = "unknown"


# =========================================================
# ML ACTION OUTCOME STORE
# =========================================================
class MLActionOutcome(Base):
    """
    Stores AI action decisions and their observed outcomes.

    One row = one AI action suggestion
    Outcome fields are filled later (post-observation windows)

    This table enables:
    - Supervised ML training
    - Confidence calibration
    - Rule vs ML effectiveness comparison
    """

    __tablename__ = "ml_action_outcomes"

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

    # -------------------------
    # AI DECISION CONTEXT
    # -------------------------
    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="AIActionType at decision time",
    )

    ai_confidence: Mapped[float] = mapped_column(
        Numeric(4, 3),
        nullable=False,
        doc="AI confidence score at decision time (0–1)",
    )

    ai_score: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        doc="Overall AI score at decision time (if available)",
    )

    context_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Hash of campaign + features + category context",
    )

    decided_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # -------------------------
    # OUTCOME OBSERVATION
    # -------------------------
    observed_7d_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    observed_14d_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    observed_30d_at: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    outcome_7d: Mapped[ActionOutcomeLabel] = mapped_column(
        Enum(ActionOutcomeLabel),
        nullable=False,
        default=ActionOutcomeLabel.UNKNOWN,
    )

    outcome_14d: Mapped[ActionOutcomeLabel] = mapped_column(
        Enum(ActionOutcomeLabel),
        nullable=False,
        default=ActionOutcomeLabel.UNKNOWN,
    )

    outcome_30d: Mapped[ActionOutcomeLabel] = mapped_column(
        Enum(ActionOutcomeLabel),
        nullable=False,
        default=ActionOutcomeLabel.UNKNOWN,
    )

    # -------------------------
    # PERFORMANCE DELTAS (OPTIONAL)
    # -------------------------
    delta_ctr: Mapped[float | None] = mapped_column(
        Numeric(6, 3),
        nullable=True,
    )

    delta_cpl: Mapped[float | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    delta_roas: Mapped[float | None] = mapped_column(
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


# Useful lookup index
Index(
    "ix_ml_action_outcomes_campaign_action_time",
    MLActionOutcome.campaign_id,
    MLActionOutcome.action_type,
    MLActionOutcome.decided_at,
)

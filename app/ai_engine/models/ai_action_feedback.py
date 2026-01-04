from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


# =========================================================
# AI ACTION FEEDBACK (LEARNING SIGNAL)
# =========================================================
class AIActionFeedback(Base):
    """
    Stores user feedback on AI suggestions.

    Append-only.
    Used for:
    - Rule performance evaluation
    - Confidence calibration
    - Future ML training
    """

    __tablename__ = "ai_action_feedback"

    # -------------------------
    # IDENTITY
    # -------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # -------------------------
    # CONTEXT
    # -------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    rule_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Rule that generated the action",
    )

    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="AIActionType value",
    )

    # -------------------------
    # FEEDBACK SIGNAL
    # -------------------------
    is_helpful: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        doc="User marked action as helpful or not",
    )

    confidence_at_time: Mapped[float] = mapped_column(
        nullable=False,
        doc="AI confidence score at suggestion time",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# Helpful indexes for learning queries
Index(
    "ix_ai_action_feedback_rule_action",
    AIActionFeedback.rule_name,
    AIActionFeedback.action_type,
)

Index(
    "ix_ai_action_feedback_campaign",
    AIActionFeedback.campaign_id,
)

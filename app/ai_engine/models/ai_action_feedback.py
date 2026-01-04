from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from enum import Enum

from app.core.database import Base


# =========================================================
# APPROVAL STATUS (PHASE 11)
# =========================================================
class ActionApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# =========================================================
# AI ACTION APPROVAL & FEEDBACK (PHASE 11)
# =========================================================
class AIActionFeedback(Base):
    """
    Stores approval + feedback on AI suggestions.

    Append-only.
    Used for:
    - Human approval tracking (Phase 11)
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
    # APPROVAL WORKFLOW (PHASE 11)
    # -------------------------
    approval_status: Mapped[ActionApprovalStatus] = mapped_column(
        SAEnum(ActionApprovalStatus, name="action_approval_status"),
        nullable=False,
        default=ActionApprovalStatus.DRAFT,
        doc="Human approval lifecycle state",
    )

    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who approved or rejected the action",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    approval_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Action invalid after this timestamp",
    )

    # -------------------------
    # FEEDBACK SIGNAL
    # -------------------------
    is_helpful: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        doc="User marked action as helpful or not",
    )

    confidence_at_time: Mapped[float] = mapped_column(
        nullable=False,
        doc="AI confidence score at suggestion time",
    )

    # -------------------------
    # HARD SAFETY FLAGS
    # -------------------------
    auto_execution_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="System-level block on auto execution",
    )

    rollback_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether rollback metadata exists",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================================================
# INDEXES
# =========================================================
Index(
    "ix_ai_action_feedback_rule_action",
    AIActionFeedback.rule_name,
    AIActionFeedback.action_type,
)

Index(
    "ix_ai_action_feedback_campaign",
    AIActionFeedback.campaign_id,
)

Index(
    "ix_ai_action_feedback_approval_status",
    AIActionFeedback.approval_status,
)

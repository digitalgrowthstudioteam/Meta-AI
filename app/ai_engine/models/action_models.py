from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class AIAction(Base):
    """
    Represents a single AI decision or recommendation made for a campaign.

    This table is the authoritative audit log for:
    - AI suggestions
    - Explainability
    - Approval / rejection
    - Rollback readiness
    """

    __tablename__ = "ai_actions"

    # ===============================
    # CORE IDENTITY
    # ===============================
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ===============================
    # ACTION DEFINITION
    # ===============================
    # Examples:
    # BUDGET_INCREASE, BUDGET_DECREASE, PAUSE_CAMPAIGN, SCALE_CAMPAIGN, NO_ACTION
    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # ===============================
    # OBJECTIVE CONTEXT
    # ===============================
    # LEAD or SALES
    objective_type: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # ===============================
    # TIME DEPTH (DATA WINDOW USED)
    # ===============================
    # 1D, 3D, 7D, 14D, 30D, 90D, LIFETIME
    time_window: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # ===============================
    # STATE SNAPSHOTS (ROLLBACK READY)
    # ===============================
    # Exact campaign state before suggestion
    before_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    # Suggested campaign state after applying AI recommendation
    after_state: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    # ===============================
    # EXPLAINABILITY PAYLOAD
    # ===============================
    # Stores:
    # - metrics snapshot
    # - baseline comparison
    # - thresholds breached
    # - human-readable reason
    explainability: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )

    # ===============================
    # CONFIDENCE SCORING
    # ===============================
    # LOW / MEDIUM / HIGH
    confidence_level: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    # ===============================
    # ACTION LIFECYCLE
    # ===============================
    # SUGGESTED / APPROVED / REJECTED / APPLIED / ROLLED_BACK
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="SUGGESTED"
    )

    # ===============================
    # EXECUTION MODE (FUTURE-READY)
    # ===============================
    # SUGGEST (Phase 8A)
    # AUTO (explicitly disabled until future phase)
    executed_mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="SUGGEST"
    )

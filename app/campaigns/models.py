from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class Campaign(Base):
    """
    Canonical Campaign model.

    This table is the SINGLE SOURCE OF TRUTH for:
    - Meta campaign visibility
    - AI activation state
    - Billing ownership
    - Enforcement & limits
    - Audit & rollback readiness
    """

    __tablename__ = "campaigns"

    # =========================
    # PRIMARY IDENTIFIERS
    # =========================
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    meta_campaign_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    ad_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meta_ad_accounts.id"),
        nullable=False,
        index=True,
    )

    # =========================
    # META SNAPSHOT (READ-ONLY)
    # =========================
    name: Mapped[str] = mapped_column(String, nullable=False)

    objective: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="LEAD or SALES (never mixed)",
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="ACTIVE / PAUSED / ARCHIVED (Meta state)",
    )

    last_meta_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Last successful Meta fetch",
    )

    # =========================
    # AI CONTROL & ENFORCEMENT
    # =========================
    ai_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    ai_activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ai_deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ai_lock_reason: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc=(
            "Why AI cannot be activated. "
            "Examples: TRIAL_LIMIT, PLAN_LIMIT, EXPIRED, ADMIN_LOCK"
        ),
    )

    # =========================
    # BILLING OWNERSHIP
    # =========================
    is_trial_campaign: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Counts against trial limits",
    )

    is_manual_paid: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Manually purchased campaign",
    )

    manual_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expiry date for manual purchases",
    )

    # =========================
    # ADMIN & SAFETY
    # =========================
    admin_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Admin hard lock (kill switch)",
    )

    # =========================
    # LIFECYCLE
    # =========================
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Soft delete — never remove Meta history",
    )

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


# =========================
# INDEXES (PERFORMANCE)
# =========================
Index(
    "ix_campaign_account_ai_active",
    Campaign.ad_account_id,
    Campaign.ai_active,
)

Index(
    "ix_campaign_billing",
    Campaign.is_trial_campaign,
    Campaign.is_manual_paid,
)

from datetime import datetime, date, timedelta
from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Date,
    Integer,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.base import Base
from app.plans.models import Plan


class Subscription(Base):
    __tablename__ = "subscriptions"

    # =====================================================
    # CORE IDENTIFIERS
    # =====================================================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # PLAN LINK
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # PAYMENT LINK (PHASE 19)
    # =====================================================
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Payment that activated this subscription",
    )

    # =====================================================
    # SUBSCRIPTION STATE
    # =====================================================
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="trial | active | expired | cancelled",
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # TRIAL METADATA
    # =====================================================
    is_trial: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    trial_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    trial_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    grace_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # SNAPSHOTS & FLAGS
    # =====================================================
    ai_campaign_limit_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    assigned_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # AUDIT
    # =====================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    plan = relationship(
        Plan,
        lazy="selectin",
    )

    addons = relationship(
        "SubscriptionAddon",
        back_populates="subscription",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # =====================================================
    # 🔒 DB-LEVEL SAFETY (CRITICAL)
    # =====================================================
    __table_args__ = (
        Index(
            "uq_active_subscription_per_user",
            "user_id",
            unique=True,
            postgresql_where=(
                (status.in_(["trial", "active"]))
            ),
        ),
    )


# =========================================================
# NEW: SUBSCRIPTION ADD-ON MODEL
# =========================================================
class SubscriptionAddon(Base):
    """
    Represents purchased add-on capacity for AI campaigns.
    Each addon increases limit by `extra_ai_campaigns`.

    Business rules:
      - Addon expires in 30 days
      - Effective expiry = min(addon_expiry, subscription_expiry)
      - Agency plan only (handled in service layer)
    """

    __tablename__ = "subscription_addons"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Number of additional campaigns this addon gives
    extra_ai_campaigns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    purchased_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # RELATIONSHIP
    subscription = relationship(
        Subscription,
        back_populates="addons",
        lazy="selectin",
    )

    # =====================================================
    # HELPERS
    # =====================================================
    def compute_default_expiry(self) -> datetime:
        """Default 30-day expiry."""
        return self.purchased_at + timedelta(days=30)

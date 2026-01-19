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
    """
    Subscription lifecycle (UTC timestamps stored):

    trial  → active → grace → expired

    Grace period is applied only after paid expiry (3 days).
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Links to Plan
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Links to Payment (nullable for trial)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status: trial | active | grace | expired
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # UTC timestamps (converted to IST for display)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Trial fields (UTC aligned)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Grace period (UTC)
    grace_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="After ends_at + grace period, subscription moves to expired",
    )

    # Snapshot of plan limits at purchase time
    ai_campaign_limit_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Convenience flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationship
    plan = relationship(Plan, lazy="selectin")

    addons = relationship(
        "SubscriptionAddon",
        back_populates="subscription",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "uq_active_subscription_per_user",
            "user_id",
            unique=True,
            postgresql_where=(status.in_(["trial", "active", "grace"])),
        ),
    )


class SubscriptionAddon(Base):
    """
    Add-on slots for agency accounts.
    Example: extra AI campaigns = +5 Slots
    """

    __tablename__ = "subscription_addons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Add-ons always represent extra AI slots
    extra_ai_campaigns: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Consumption audit (one-time lock)
    consumed_by_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Campaign that consumed this slot (immutable once set)",
    )

    # UTC timestamps
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    subscription = relationship(Subscription, back_populates="addons", lazy="selectin")

    def compute_default_expiry(self) -> datetime:
        return self.purchased_at + timedelta(days=30)

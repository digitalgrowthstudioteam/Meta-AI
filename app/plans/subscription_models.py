from datetime import datetime, date
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Date, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.base import Base
from app.plans.models import Plan


class Subscription(Base):
    """
    Subscription lifecycle:

    trial → active → grace → expired → cancelled

    Billing cycles:
      - monthly (Razorpay recurring)
      - yearly (Prepaid order)
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

    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # trial | active | grace | expired | cancelled
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # billing cycle: monthly | yearly | trial | custom
    billing_cycle: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="monthly | yearly | trial | custom",
    )

    # ENTERPRISE-CUSTOM BILLING
    pricing_mode: Mapped[str] = mapped_column(
        String,
        default="standard",
        nullable=False,
        doc="standard | custom",
    )

    custom_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Custom enterprise price in paise",
    )

    custom_duration_months: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Custom billing duration in months",
    )

    never_expires: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="If true, ends_at is ignored",
    )

    admin_notes: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Admin internal notes",
    )

    # UTC timestamps
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # TRIAL
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Grace
    grace_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Cancel
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Razorpay recurring link
    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Set only for monthly recurring",
    )

    # snapshot limits
    ai_campaign_limit_snapshot: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

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

    extra_ai_campaigns: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    consumed_by_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

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

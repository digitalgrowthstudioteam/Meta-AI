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

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

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

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

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

    __table_args__ = (
        Index(
            "uq_active_subscription_per_user",
            "user_id",
            unique=True,
            postgresql_where=(status.in_(["trial", "active"])),
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

    subscription = relationship(
        Subscription,
        back_populates="addons",
        lazy="selectin",
    )

    def compute_default_expiry(self) -> datetime:
        return self.purchased_at + timedelta(days=30)

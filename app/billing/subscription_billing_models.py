from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey

from app.core.base import Base
from app.users.models import User
from app.plans.models import Plan


class SubscriptionBilling(Base):
    """
    Razorpay Billing Subscription Tracker

    Covers:
    - Monthly recurring: uses Razorpay subscription object
    - Yearly prepaid: treated as subscription_yearly (12 months from purchase)

    Note:
    - User-level active plan state is managed in app.plans.subscription_models.Subscription
    - This model tracks ONLY billing lifecycle
    """

    __tablename__ = "subscription_billing"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
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

    # Razorpay identifiers
    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Set for monthly recurring subscriptions",
    )

    razorpay_customer_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Optional Razorpay customer link",
    )

    # Billing Cycle: monthly | yearly
    billing_cycle: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="monthly or yearly",
    )

    # Lifecycle state
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="active",
        doc="active | past_due | canceled | completed",
    )

    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="If true, cancel after current billing cycle",
    )

    # Period windows (IST converted timestamps stored as UTC)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    current_period_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    next_charge_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Next expected Razorpay charge_time for monthly mode",
    )

    grace_end_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Grace period end (3 days after current_period_end)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(User, lazy="selectin")
    plan = relationship(Plan, lazy="selectin")

    # =========================================================
    # HELPERS — YEARLY LOGIC (OPTION 2)
    # =========================================================
    @staticmethod
    def compute_yearly_period(start: datetime) -> tuple[datetime, datetime, datetime]:
        """
        Returns: (period_start, period_end, grace_end)
        Yearly plan = 12 months from purchase + 3-day grace
        """
        end = start + timedelta(days=365)
        grace = end + timedelta(days=3)
        return start, end, grace

    # =========================================================
    # HELPERS — MONTHLY LOGIC (RAZORPAY)
    # =========================================================
    @staticmethod
    def compute_monthly_period(start: datetime) -> tuple[datetime, datetime, datetime]:
        """
        Returns: (period_start, period_end, grace_end)
        Monthly = 30 days from start + 3-day grace
        """
        end = start + timedelta(days=30)
        grace = end + timedelta(days=3)
        return start, end, grace

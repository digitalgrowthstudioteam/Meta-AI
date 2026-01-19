from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Payment(Base):
    """
    Razorpay Payment Record (Unified for all billing modes)

    Supported types:
        - subscription           (recurring monthly)
        - subscription_yearly    (one-time prepaid yearly)
        - manual_campaign        (one-time campaign purchase)
        - addon                  (one-time addon purchase)

    Status lifecycle mirrors Razorpay:
        created -> authorized -> captured -> refunded -> failed
    """

    __tablename__ = "payments"

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

    # ------------------------------------------------
    # Razorpay identifiers
    # ------------------------------------------------
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Set for one-time payments (yearly/addon/manual/etc)",
    )

    razorpay_subscription_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
        doc="Set for monthly recurring subscriptions",
    )

    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    razorpay_signature: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # ------------------------------------------------
    # Amount & Status
    # ------------------------------------------------
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Amount in paise (smallest INR unit)",
    )

    currency: Mapped[str] = mapped_column(
        String,
        default="INR",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="created | authorized | captured | refunded | failed",
    )

    # ------------------------------------------------
    # Business fields
    # ------------------------------------------------
    payment_for: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="subscription | subscription_yearly | manual_campaign | addon",
    )

    # Plan reference (only for subscription types)
    plan_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Plan ID for subscription & subscription_yearly",
    )

    # UUID-based reference (manual campaign ID, addon ID, etc)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Used for manual campaign / addon / future",
    )

    # ------------------------------------------------
    # Timestamps
    # ------------------------------------------------
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="Set when payment is fully captured",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =====================================================
# INDEXES (Query Optimized)
# =====================================================
Index("ix_payment_user_created", Payment.user_id, Payment.created_at)
Index("ix_payment_status", Payment.status)
Index("ix_payment_order", Payment.razorpay_order_id)
Index("ix_payment_subscription", Payment.razorpay_subscription_id)

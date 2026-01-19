from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Payment(Base):
    """
    Unified payment record covering:
    - subscription (monthly recurring)
    - subscription_yearly (one-time yearly)
    - addon
    - manual_campaign

    New fields:
      - billing_cycle (monthly/yearly)
      - mode (subscription/payg)
      - gst
      - valid_until
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

    # Razorpay mapping
    razorpay_order_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    razorpay_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String, nullable=True)

    # Amount
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String, default="INR", nullable=False)

    # created | authorized | captured | refunded | failed
    status: Mapped[str] = mapped_column(String, nullable=False)

    # subscription | subscription_yearly | manual_campaign | addon
    payment_for: Mapped[str] = mapped_column(String, nullable=False)

    # subscription/payg
    mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="subscription",
        doc="subscription | payg",
    )

    # monthly | yearly
    billing_cycle: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="monthly | yearly | null",
    )

    # Plan association
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # manual reference
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # GST
    gst_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gst_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


Index("ix_payment_user_created", Payment.user_id, Payment.created_at)
Index("ix_payment_status", Payment.status)
Index("ix_payment_order", Payment.razorpay_order_id)
Index("ix_payment_subscription", Payment.razorpay_subscription_id)

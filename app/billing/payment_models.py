from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Payment(Base):
    """
    Razorpay payment record (immutable after success).

    Covers:
    - Subscription purchase
    - Manual campaign purchase
    - Add-ons (future)
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

    # -------------------------
    # Razorpay identifiers
    # -------------------------
    razorpay_order_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
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

    # -------------------------
    # Amount & status
    # -------------------------
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Amount in paise",
    )

    currency: Mapped[str] = mapped_column(
        String,
        default="INR",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="created | authorized | captured | failed | refunded",
    )

    # -------------------------
    # Business reference
    # -------------------------
    payment_for: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="subscription | manual_campaign | addon",
    )

    related_reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="Subscription ID / Campaign ID / Addon ID",
    )

    # -------------------------
    # Timestamps
    # -------------------------
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =====================================================
# INDEXES
# =====================================================
Index("ix_payment_user_created", Payment.user_id, Payment.created_at)
Index("ix_payment_status", Payment.status)

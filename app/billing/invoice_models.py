from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    # -----------------------------
    # CORE IDS
    # -----------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # -----------------------------
    # INVOICE IDENTITY
    # -----------------------------
    invoice_number: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    invoice_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # -----------------------------
    # BILLING DETAILS
    # -----------------------------
    billing_name: Mapped[str] = mapped_column(String, nullable=False)
    billing_email: Mapped[str] = mapped_column(String, nullable=False)

    # -----------------------------
    # AMOUNTS (PAISE)
    # -----------------------------
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)

    currency: Mapped[str] = mapped_column(
        String,
        default="INR",
        nullable=False,
    )

    # -----------------------------
    # PERIOD (FOR SUBSCRIPTIONS)
    # -----------------------------
    period_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period_to: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # -----------------------------
    # STATUS & FILE
    # -----------------------------
    status: Mapped[str] = mapped_column(
        String,
        default="paid",
        nullable=False,
        doc="paid | refunded | void",
    )

    invoice_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # -----------------------------
    # AUDIT
    # -----------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

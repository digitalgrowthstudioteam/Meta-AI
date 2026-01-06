from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    # -----------------------------
    # CORE IDS
    # -----------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payments.id"), unique=True, index=True
    )

    # -----------------------------
    # INVOICE IDENTITY
    # -----------------------------
    invoice_number: Mapped[str] = mapped_column(
        String, unique=True, index=True
    )
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # -----------------------------
    # BILLING DETAILS
    # -----------------------------
    billing_name: Mapped[str] = mapped_column(String)
    billing_email: Mapped[str] = mapped_column(String)

    # -----------------------------
    # AMOUNTS (PAISE)
    # -----------------------------
    subtotal: Mapped[int] = mapped_column(Integer)
    tax_amount: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer)

    currency: Mapped[str] = mapped_column(
        String, default="INR"
    )

    # -----------------------------
    # PERIOD (FOR SUBSCRIPTIONS)
    # -----------------------------
    period_from: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    period_to: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    # -----------------------------
    # STATUS & FILE
    # -----------------------------
    status: Mapped[str] = mapped_column(
        String, default="paid"
    )  # paid | refunded | void
    invoice_url: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    # -----------------------------
    # AUDIT
    # -----------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

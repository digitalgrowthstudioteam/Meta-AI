from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id"))

    invoice_number: Mapped[str] = mapped_column(String, unique=True)
    invoice_date: Mapped[datetime] = mapped_column(DateTime)

    billing_name: Mapped[str] = mapped_column(String)
    billing_email: Mapped[str] = mapped_column(String)

    subtotal: Mapped[int] = mapped_column(Integer)
    tax_amount: Mapped[int] = mapped_column(Integer)
    total_amount: Mapped[int] = mapped_column(Integer)

    invoice_url: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

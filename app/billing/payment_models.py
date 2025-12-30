from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    razorpay_payment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String)
    razorpay_signature: Mapped[str | None] = mapped_column(String, nullable=True)

    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String, default="INR")
    status: Mapped[str] = mapped_column(String)

    payment_for: Mapped[str] = mapped_column(String)
    related_reference_id: Mapped[uuid.UUID] = mapped_column()

    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from typing import Optional

from app.core.base import Base
from app.auth.models import Session


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String)

    role: Mapped[str] = mapped_column(
        String,
        default="user",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    razorpay_customer_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    sessions = relationship(
        Session,
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

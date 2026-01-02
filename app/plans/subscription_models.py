from datetime import datetime, date
import uuid

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("plans.id"),
        nullable=True,
    )

    # Trial (legacy)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_ai_campaign_limit: Mapped[int] = mapped_column(Integer, default=3)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Enforcement
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    grace_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    ai_campaign_limit_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships — STRING BASED (SAFE NOW)
    user = relationship("User")
    plan = relationship("Plan")

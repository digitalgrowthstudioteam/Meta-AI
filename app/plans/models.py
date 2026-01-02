from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String, unique=True)

    monthly_price: Mapped[int] = mapped_column(Integer)
    max_ai_campaigns: Mapped[int] = mapped_column(Integer)
    allows_addons: Mapped[bool] = mapped_column(Boolean, default=False)

    # New enforcement
    price_monthly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_campaign_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_trial_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

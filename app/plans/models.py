from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    # Pricing (paise)
    monthly_price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Monthly price in smallest currency unit (e.g. paise)",
    )

    # Limits
    max_ai_campaigns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Max AI-active campaigns allowed",
    )

    max_ad_accounts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Max connected Meta ad accounts",
    )

    allows_addons: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Trial policy
    is_trial_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    trial_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

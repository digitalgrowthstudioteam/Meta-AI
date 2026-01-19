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

    # ======================
    # PRICING (IN PAISE)
    # ======================
    monthly_price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Monthly recurring price in paise",
    )

    yearly_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Yearly prepaid price in paise (25% discount applied)",
    )

    # ======================
    # RAZORPAY PLAN MAPPING
    # ======================
    razorpay_monthly_plan_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Razorpay subscription plan id for monthly recurring",
    )

    razorpay_yearly_plan_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Razorpay order plan id (yearly prepaid, not recurring)",
    )

    # ======================
    # LIMITS
    # ======================
    max_ai_campaigns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Max AI-active campaigns allowed",
    )

    max_ad_accounts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Max connected Meta ad accounts (NULL = unlimited)",
    )

    # optional: team seats later if required
    max_team_members: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Team seats (NULL = unlimited)",
    )

    allows_addons: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ======================
    # TRIAL POLICY
    # ======================
    is_trial_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    trial_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Trial duration in days",
    )

    # ======================
    # STATUS
    # ======================
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

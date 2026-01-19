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
    )

    yearly_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # ======================
    # RAZORPAY PLAN MAPPING
    # ======================
    razorpay_monthly_plan_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    razorpay_yearly_plan_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    # ======================
    # LIMITS
    # ======================
    max_ai_campaigns: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_ad_accounts: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    max_team_members: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
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
    )

    # ======================
    # PLAN CAPS / USER MODES
    # ======================
    auto_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    manual_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    yearly_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ======================
    # VISIBILITY (Enterprise hidden)
    # ======================
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
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

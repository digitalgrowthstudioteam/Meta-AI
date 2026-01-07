from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Plan(Base):
    __tablename__ = "plans"

    # =====================================================
    # CORE IDENTIFIER
    # =====================================================
    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    # =====================================================
    # CANONICAL PRICING & LIMITS (SINGLE SOURCE)
    # =====================================================
    price_monthly: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Monthly price in smallest currency unit (e.g. paise)",
    )

    ai_campaign_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Max AI-active campaigns allowed by this plan",
    )

    allows_addons: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # TRIAL POLICY (PLAN-LEVEL ONLY)
    # =====================================================
    is_trial_allowed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    trial_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # =====================================================
    # STATUS & AUDIT
    # =====================================================
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

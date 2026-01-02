from datetime import datetime
import uuid

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Plan(Base):
    """
    System-owned plan definitions.

    IMPORTANT:
    - Old columns are intentionally retained (deprecated)
    - New columns are added for STEP 8 enforcement
    - No destructive changes allowed in this phase
    """

    __tablename__ = "plans"

    # 🔒 EXISTING PK (DO NOT CHANGE TYPE IN DB)
    id: Mapped[int] = mapped_column(primary_key=True)

    # ======================
    # EXISTING (DEPRECATED)
    # ======================
    name: Mapped[str] = mapped_column(String, unique=True)

    # OLD pricing / limits (kept for backward compatibility)
    monthly_price: Mapped[int] = mapped_column(Integer)
    max_ai_campaigns: Mapped[int] = mapped_column(Integer)
    allows_addons: Mapped[bool] = mapped_column(Boolean, default=False)

    # ======================
    # NEW (ENFORCEMENT)
    # ======================
    price_monthly: Mapped[int | None] = mapped_column(Integer, nullable=True)  # paise
    ai_campaign_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_trial_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

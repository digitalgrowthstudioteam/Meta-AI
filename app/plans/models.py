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

from app.core.database import Base


class Plan(Base):
    """
    System-owned plan definitions.
    Plans define WHAT is allowed.
    They never expire.
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    price_monthly: Mapped[int] = mapped_column(Integer, nullable=False)  # paise

    ai_campaign_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    max_ad_accounts: Mapped[int] = mapped_column(Integer, nullable=False)

    is_trial_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

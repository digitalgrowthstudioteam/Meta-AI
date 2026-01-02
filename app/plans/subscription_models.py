from datetime import datetime, date
import uuid

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Date,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

# ✅ CRITICAL: import Plan so mapper can resolve it
from app.plans.models import Plan


class Subscription(Base):
    __tablename__ = "subscriptions"

    # =====================================================
    # CORE IDENTIFIERS
    # =====================================================
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # SUBSCRIPTION STATE
    # =====================================================
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="trial | active | expired | cancelled",
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # TRIAL METADATA (OPTION B — LOCKED)
    # =====================================================
    is_trial: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    trial_start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    trial_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    grace_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =====================================================
    # SNAPSHOTS & FLAGS
    # =====================================================
    ai_campaign_limit_snapshot: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    assigned_by_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # =====================================================
    # AUDIT
    # =====================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    plan = relationship(
        Plan,
        lazy="selectin",
    )

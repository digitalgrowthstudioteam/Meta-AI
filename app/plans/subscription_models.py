from datetime import datetime, date

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Date,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.plans.models import Plan


class Subscription(Base):
    __tablename__ = "subscriptions"

    # =====================================================
    # CORE IDENTIFIERS
    # =====================================================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 🔒 OPTION A — INTEGER PLAN ID (LOCKED)
    plan_id: Mapped[int] = mapped_column(
        Integer,
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
    # TRIAL METADATA (OPTION A)
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
        Integer,
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

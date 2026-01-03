from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
import uuid

from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    # =========================
    # PRIMARY IDENTIFIERS
    # =========================
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    meta_campaign_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    ad_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meta_ad_accounts.id"),
        nullable=False,
        index=True,
    )

    # =========================
    # META SNAPSHOT (READ-ONLY)
    # =========================
    name: Mapped[str] = mapped_column(String, nullable=False)

    objective: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    last_meta_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =========================
    # AI CONTROL (PHASE 1)
    # =========================
    ai_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    ai_activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =========================
    # BILLING (CURRENT DB)
    # =========================
    is_manual: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    manual_expiry_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # =========================
    # LIFECYCLE
    # =========================
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================
# INDEXES
# =========================
Index(
    "ix_campaign_account_ai_active",
    Campaign.ad_account_id,
    Campaign.ai_active,
)

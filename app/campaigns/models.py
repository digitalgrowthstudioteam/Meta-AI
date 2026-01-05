from sqlalchemy import (
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Float,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
import uuid

from app.core.database import Base
from app.ai_engine.models.campaign_category_map import CampaignCategoryMap


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
    objective: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)

    last_meta_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # =========================
    # AI CONTROL
    # =========================
    ai_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    ai_activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_deactivated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # =========================
    # PHASE 11 — EXECUTION GUARDRAILS
    # =========================
    ai_execution_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Hard lock: prevents any auto execution",
    )

    ai_max_budget_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_budget_floor: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_budget_ceiling: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_execution_window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ai_execution_window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # =========================
    # PHASE 11 — MANUAL CAMPAIGN PURCHASE (SOURCE OF TRUTH)
    # =========================
    is_manual: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="True if campaign is manually purchased",
    )

    manual_purchased_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        doc="When manual campaign was purchased",
    )

    manual_valid_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Manual campaign validity start",
    )

    manual_valid_till: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Manual campaign validity end",
    )

    manual_purchase_plan: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="0-5 | 6-29 | 30+",
    )

    manual_price_paid: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Amount paid for manual campaign",
    )

    manual_status: Mapped[str] = mapped_column(
        String,
        default="inactive",
        nullable=False,
        doc="inactive | active | expired | revoked",
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
    # CATEGORY VISIBILITY (PHASE 9.2 — READ ONLY)
    # =========================
    category_map: Mapped[CampaignCategoryMap | None] = relationship(
        CampaignCategoryMap,
        primaryjoin="Campaign.id == CampaignCategoryMap.campaign_id",
        uselist=False,
        viewonly=True,
    )


# =========================================================
# PHASE 10 — CAMPAIGN ACTION HISTORY (IMMUTABLE LOG)
# =========================================================
class CampaignActionLog(Base):
    __tablename__ = "campaign_action_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    actor_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="user | ai | admin | system",
    )

    action_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="ai_toggle | manual_purchase | manual_expiry | rollback",
    )

    before_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False)

    reason: Mapped[str | None] = mapped_column(String, nullable=True)

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

Index(
    "ix_campaign_manual_status",
    Campaign.is_manual,
    Campaign.manual_status,
)

Index(
    "ix_campaign_action_log_campaign_time",
    CampaignActionLog.campaign_id,
    CampaignActionLog.created_at,
)

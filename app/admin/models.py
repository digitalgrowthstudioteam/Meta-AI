from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    String,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


# =====================================================
# ADMIN AUDIT LOGS (PHASE 6 — IMMUTABLE)
# =====================================================
class AdminAuditLog(Base):
    """
    Immutable admin/system audit log.
    Used for compliance, rollback, and traceability.
    """

    __tablename__ = "admin_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    admin_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_type = Column(
        String(64),
        nullable=False,
        index=True,
        doc="user | campaign | subscription | billing | system | feature_flag",
    )

    target_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    action = Column(
        String(128),
        nullable=False,
        index=True,
    )

    before_state = Column(
        JSONB,
        nullable=False,
    )

    after_state = Column(
        JSONB,
        nullable=False,
    )

    reason = Column(
        Text,
        nullable=False,
    )

    rollback_token = Column(
        UUID(as_uuid=True),
        nullable=True,
        unique=True,
        index=True,
    )

    ip_address = Column(
        String(64),
        nullable=True,
    )

    user_agent = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


# =====================================================
# ADMIN OVERRIDES
# =====================================================
class AdminOverride(Base):
    """
    Temporary, auditable admin-level overrides.
    Never mutates plans or subscriptions.
    """

    __tablename__ = "admin_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    extra_ai_campaigns = Column(Integer, default=0, nullable=False)

    force_ai_enabled = Column(Boolean, default=False, nullable=False)

    override_expires_at = Column(DateTime(timezone=True), nullable=True)

    reason = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


# =====================================================
# GLOBAL SYSTEM SETTINGS (SINGLE ROW)
# =====================================================
class GlobalSettings(Base):
    """
    Global, system-wide admin-controlled settings.
    """

    __tablename__ = "global_settings"
    __table_args__ = (
        UniqueConstraint("singleton_key", name="uq_global_settings_singleton"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    singleton_key = Column(Integer, nullable=False, default=1)

    # ---------------------------------
    # PLATFORM BASICS
    # ---------------------------------
    site_name = Column(Text, nullable=False, default="Digital Growth Studio")
    dashboard_title = Column(Text, nullable=False, default="Meta Ads AI Platform")
    logo_url = Column(Text, nullable=True)

    # ---------------------------------
    # CORE SYSTEM SWITCHES
    # ---------------------------------
    ai_globally_enabled = Column(Boolean, default=True, nullable=False)
    meta_sync_enabled = Column(Boolean, default=True, nullable=False)
    maintenance_mode = Column(Boolean, default=False, nullable=False)

    # =================================================
    # PHASE P2 — GLOBAL AI CONTROLS (NEW)
    # =================================================
    expansion_mode_enabled = Column(Boolean, default=True, nullable=False)
    fatigue_mode_enabled = Column(Boolean, default=True, nullable=False)
    auto_pause_enabled = Column(Boolean, default=True, nullable=False)
    confidence_gating_enabled = Column(Boolean, default=True, nullable=False)

    # =================================================
    # PHASE P2 — AI THROTTLING (NEW)
    # =================================================
    max_optimizations_per_day = Column(Integer, default=100, nullable=False)
    max_expansions_per_day = Column(Integer, default=50, nullable=False)
    ai_refresh_frequency_minutes = Column(Integer, default=60, nullable=False)

    # =================================================
    # META API SETTINGS (PHASE 7.2)
    # =================================================
    meta_sync_lookback_days = Column(Integer, default=30, nullable=False)

    allowed_objectives = Column(
        ARRAY(String),
        default=["LEAD_GENERATION", "CONVERSIONS", "TRAFFIC"],
        nullable=False,
    )

    whitelisted_ad_accounts = Column(
        ARRAY(String),
        default=[],
        nullable=False,
    )

    token_refresh_mode = Column(String, default="auto", nullable=False)
    webhook_validation_mode = Column(String, default="strict", nullable=False)

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

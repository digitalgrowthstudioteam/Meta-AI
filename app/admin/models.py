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
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


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
# PHASE 14.4 — GLOBAL SYSTEM SETTINGS (SINGLE ROW)
# =====================================================
class GlobalSettings(Base):
    """
    Global, system-wide admin-controlled settings.

    🔒 RULES:
    - Exactly ONE row exists
    - All changes must be audited (via CampaignActionLog or future SystemLog)
    - No environment dependence
    """

    __tablename__ = "global_settings"
    __table_args__ = (
        UniqueConstraint("singleton_key", name="uq_global_settings_singleton"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Enforces single-row pattern
    singleton_key = Column(
        Integer,
        nullable=False,
        default=1,
    )

    # -------------------------
    # BRANDING
    # -------------------------
    site_name = Column(
        Text,
        nullable=False,
        default="Digital Growth Studio",
    )

    dashboard_title = Column(
        Text,
        nullable=False,
        default="Meta Ads AI Platform",
    )

    logo_url = Column(
        Text,
        nullable=True,
        doc="Public URL to logo asset",
    )

    # -------------------------
    # GLOBAL KILL SWITCHES
    # -------------------------
    ai_globally_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Master AI enable/disable switch",
    )

    meta_sync_enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        doc="Disables all Meta fetch/sync when false",
    )

    maintenance_mode = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="When enabled, non-admin users are blocked",
    )

    # -------------------------
    # AUDIT
    # -------------------------
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

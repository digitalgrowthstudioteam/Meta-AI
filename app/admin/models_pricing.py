from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Text,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


# =====================================================
# ADMIN PRICING CONFIG (PHASE 7 — VERSIONED, AUDITED)
# =====================================================
class AdminPricingConfig(Base):
    """
    Admin-controlled pricing & monetization configuration.
    - Versioned
    - Audited via AdminAuditLog
    - Read-only for runtime enforcement
    - No direct coupling with plans/subscriptions
    """

    __tablename__ = "admin_pricing_configs"
    __table_args__ = (
        UniqueConstraint("version", name="uq_admin_pricing_version"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Incremental version number (1, 2, 3...)
    version = Column(
        Integer,
        nullable=False,
        index=True,
    )

    # Exactly one active config at any time
    is_active = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # =========================
    # PRICING DEFINITIONS
    # =========================
    # Example structure:
    # {
    #   "basic": {"monthly_price": 99900},
    #   "pro": {"monthly_price": 199900}
    # }
    plan_pricing = Column(
        JSONB,
        nullable=False,
        doc="Plan price definitions keyed by plan name",
    )

    # =========================
    # SLOT / ADDON DEFINITIONS
    # =========================
    # Example:
    # {
    #   "ai_campaign_slot": {
    #       "price": 49900,
    #       "valid_days": 30
    #   }
    # }
    slot_packs = Column(
        JSONB,
        nullable=False,
        doc="Addon / slot pack pricing and validity rules",
    )

    # =========================
    # TAX & CURRENCY
    # =========================
    currency = Column(
        String(8),
        nullable=False,
        default="INR",
    )

    tax_percentage = Column(
        Integer,
        nullable=False,
        default=18,
        doc="GST or tax percentage",
    )

    # =========================
    # INVOICE METADATA
    # =========================
    invoice_prefix = Column(
        String(32),
        nullable=False,
        default="DGS",
    )

    invoice_notes = Column(
        Text,
        nullable=True,
    )

    # =========================
    # PAYMENT GATEWAY MODE
    # =========================
    razorpay_mode = Column(
        String(16),
        nullable=False,
        default="live",
        doc="test | live",
    )

    # =========================
    # AUDIT METADATA
    # =========================
    created_by_admin_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    activated_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

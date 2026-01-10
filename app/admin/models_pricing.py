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
# ADMIN PRICING CONFIG (PHASE 7 — VERSIONED & AUDITED)
# =====================================================
class AdminPricingConfig(Base):
    """
    Admin-controlled pricing & monetization configuration.
    - Versioned
    - Audited
    - Read-only for runtime enforcement
    - Exactly ONE active version at any time
    """

    __tablename__ = "admin_pricing_configs"
    __table_args__ = (
        UniqueConstraint(
            "is_active",
            name="uq_single_active_pricing_config",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # =========================
    # VERSIONING
    # =========================
    version = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Monotonic version number",
    )

    is_active = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Only one config can be active",
    )

    # =========================
    # PRICING DEFINITIONS
    # =========================
    currency = Column(
        String(8),
        nullable=False,
        default="INR",
    )

    plans = Column(
        JSONB,
        nullable=False,
        doc="""
        Plan pricing overrides.
        Example:
        {
          "basic": {"monthly_price": 99900},
          "pro": {"monthly_price": 199900}
        }
        """,
    )

    slot_packs = Column(
        JSONB,
        nullable=False,
        doc="""
        Campaign slot packs.
        Example:
        [
          {"slots": 1, "price": 49900, "valid_days": 30},
          {"slots": 3, "price": 129900, "valid_days": 30}
        ]
        """,
    )

    # =========================
    # TAX & INVOICE
    # =========================
    gst_percent = Column(
        Integer,
        nullable=False,
        default=18,
        doc="GST percentage",
    )

    invoice_metadata = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="""
        Static invoice metadata.
        Example:
        {
          "company_name": "",
          "company_address": "",
          "gstin": ""
        }
        """,
    )

    # =========================
    # PAYMENT GATEWAY
    # =========================
    razorpay_mode = Column(
        String(8),
        nullable=False,
        default="live",
        doc="test | live",
    )

    # =========================
    # AUDIT FIELDS
    # =========================
    created_by_admin_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    reason = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

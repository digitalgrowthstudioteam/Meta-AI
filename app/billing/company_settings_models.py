from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class BillingCompanySettings(Base):
    """
    Singleton billing/legal entity info for invoices.
    Supports GST & non-GST suppliers.
    """

    __tablename__ = "billing_company_settings"
    __table_args__ = (
        UniqueConstraint("singleton_key", name="uq_billing_company_settings_singleton"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # enforce single row pattern via static singleton key = 1
    singleton_key = Column(
        Integer,
        nullable=False,
        default=1,
    )

    # Company legal details
    company_name = Column(Text, nullable=False)
    address_line1 = Column(Text, nullable=False)
    address_line2 = Column(Text, nullable=True)
    state = Column(String(64), nullable=False)
    state_code = Column(String(4), nullable=False)

    # Optional contact
    contact_email = Column(String(256), nullable=True)
    contact_phone = Column(String(64), nullable=True)

    # Tax fields
    gst_registered = Column(Boolean, nullable=False, default=False)
    gstin = Column(String(32), nullable=True)

    # SAC (service classification)
    sac_code = Column(String(16), nullable=True)

    # Audit
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

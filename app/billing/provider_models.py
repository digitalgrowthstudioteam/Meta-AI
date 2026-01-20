import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class BillingProvider(Base):
    """
    Stores provider credentials (encrypted) for billing systems.

    - Supports TEST + LIVE modes separately
    - Supports multiple providers (future-proof)
    - key_secret is stored encrypted using CryptoService
    """

    __tablename__ = "billing_providers"
    __table_args__ = (
        UniqueConstraint("provider", "mode", name="uq_billing_provider_mode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # e.g. 'razorpay'
    provider: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )

    # TEST | LIVE
    mode: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        doc="TEST or LIVE",
    )

    # Public key (safe)
    key_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Encrypted secret key (Fernet)
    key_secret_encrypted: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    # Optional: Razorpay webhook secret (encrypted)
    webhook_secret_encrypted: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

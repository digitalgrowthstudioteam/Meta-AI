from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

from app.core.database import Base


# =========================================================
# GLOBAL META AD ACCOUNT (NO OWNERSHIP)
# =========================================================
class MetaAdAccount(Base):
    """
    Global Meta Ad Account.
    One row per Meta Ad Account across the platform.
    """

    __tablename__ = "meta_ad_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    meta_account_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )

    account_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================================================
# USER ↔ META AD ACCOUNT ACCESS MAPPING
# =========================================================
class UserMetaAdAccount(Base):
    """
    Maps users to Meta Ad Accounts with role-based access.
    """

    __tablename__ = "user_meta_ad_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "meta_ad_account_id",
            name="uq_user_meta_ad_account_access",
        ),
    )

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

    meta_ad_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meta_ad_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="owner",  # owner | agency | admin
    )

    connected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# =========================================================
# META OAUTH TOKEN (USER-SCOPED — CORRECT)
# =========================================================
class MetaOAuthToken(Base):
    """
    Stores Meta OAuth tokens (server-side only).
    OAuth is USER-based, not account-based.
    """

    __tablename__ = "meta_oauth_tokens"

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

    access_token: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    token_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

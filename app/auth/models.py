from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

# =========================================================
# AUTH SESSION MODEL (SERVER-SIDE SESSIONS)
# =========================================================
class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_token = Column(String(255), nullable=False, unique=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    # Reserved for future security/audit use
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")


Index("idx_sessions_active", Session.user_id, Session.is_active)


# =========================================================
# MAGIC LOGIN TOKEN MODEL (ONE-TIME USE)
# =========================================================
class MagicLoginToken(Base):
    __tablename__ = "magic_login_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String(255), nullable=False, index=True)

    token_hash = Column(String(255), nullable=False, unique=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    used_at = Column(DateTime(timezone=True), nullable=True)

    is_used = Column(Boolean, default=False, nullable=False)


Index("idx_magic_tokens_valid", MagicLoginToken.email, MagicLoginToken.expires_at)

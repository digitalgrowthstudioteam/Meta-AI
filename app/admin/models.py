from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


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

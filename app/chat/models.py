from datetime import datetime
import uuid

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


# =========================================================
# CHAT THREAD (ADMIN ↔ USER)
# =========================================================
class ChatThread(Base):
    """
    One conversation between:
    - 1 user
    - 1 or more admins (admin has global access)
    """

    __tablename__ = "chat_threads"

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

    subject: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Optional topic or title",
    )

    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Admin can close chat; history remains read-only",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="thread",
        lazy="selectin",
    )


# =========================================================
# CHAT MESSAGE (IMMUTABLE)
# =========================================================
class ChatMessage(Base):
    """
    Immutable message.
    NEVER updated or deleted.
    """

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="user | admin | system",
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    thread = relationship(
        "ChatThread",
        back_populates="messages",
    )


# =========================================================
# INDEXES
# =========================================================
Index(
    "ix_chat_thread_user_created",
    ChatThread.user_id,
    ChatThread.created_at,
)

Index(
    "ix_chat_message_thread_time",
    ChatMessage.thread_id,
    ChatMessage.created_at,
)

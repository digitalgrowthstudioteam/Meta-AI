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
    One immutable support thread per user.
    Admins have global visibility.
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

    status: Mapped[str] = mapped_column(
        String,
        default="open",
        nullable=False,
        doc="open | pending | closed",
    )

    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Hard lock when closed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Used for inbox ordering",
    )

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="thread",
        lazy="selectin",
        order_by="ChatMessage.created_at",
    )


# =========================================================
# CHAT MESSAGE (IMMUTABLE)
# =========================================================
class ChatMessage(Base):
    """
    Immutable chat message.
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

    sender_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="user | admin | system",
    )

    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="User ID or Admin ID; NULL for system",
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
    "ix_chat_thread_last_message",
    ChatThread.last_message_at,
)

Index(
    "ix_chat_message_thread_time",
    ChatMessage.thread_id,
    ChatMessage.created_at,
)

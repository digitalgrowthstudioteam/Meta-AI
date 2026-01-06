from datetime import datetime
from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.chat.models import ChatThread, ChatMessage
from app.users.models import User


class ChatService:
    """
    🔒 Admin ↔ User Chat Service

    Rules:
    - Admin can read/write ALL threads
    - User can read/write ONLY own thread
    - Messages are immutable
    - Closed threads are read-only
    """

    # =====================================================
    # THREADS
    # =====================================================
    @staticmethod
    async def get_or_create_thread(
        *,
        db: AsyncSession,
        user: User,
        subject: str | None = None,
    ) -> ChatThread:
        """
        Each user has exactly ONE open thread at a time.
        """

        stmt = select(ChatThread).where(
            ChatThread.user_id == user.id,
            ChatThread.is_closed.is_(False),
        )
        result = await db.execute(stmt)
        thread = result.scalar_one_or_none()

        if thread:
            return thread

        thread = ChatThread(
            user_id=user.id,
            subject=subject,
            status="open",
            is_closed=False,
            last_message_at=datetime.utcnow(),
        )

        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        return thread

    @staticmethod
    async def list_threads_for_admin(
        *,
        db: AsyncSession,
    ) -> List[ChatThread]:
        """
        Admin sees all threads, ordered by recent activity.
        """

        stmt = (
            select(ChatThread)
            .options(selectinload(ChatThread.messages))
            .order_by(ChatThread.last_message_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_thread_for_user(
        *,
        db: AsyncSession,
        user: User,
        thread_id: UUID,
    ) -> ChatThread:
        """
        User can access ONLY their own thread.
        """

        stmt = (
            select(ChatThread)
            .options(selectinload(ChatThread.messages))
            .where(
                ChatThread.id == thread_id,
                ChatThread.user_id == user.id,
            )
        )
        result = await db.execute(stmt)
        thread = result.scalar_one_or_none()

        if not thread:
            raise ValueError("Chat thread not found")

        return thread

    # =====================================================
    # MESSAGES
    # =====================================================
    @staticmethod
    async def send_message(
        *,
        db: AsyncSession,
        thread: ChatThread,
        sender: User,
        sender_type: str,
        message: str,
    ) -> ChatMessage:
        """
        Send immutable message into a thread.
        """

        if thread.is_closed:
            raise ValueError("Chat thread is closed")

        msg = ChatMessage(
            thread_id=thread.id,
            sender_id=sender.id if sender else None,
            sender_type=sender_type,
            message=message,
        )

        thread.last_message_at = datetime.utcnow()
        thread.status = "pending" if sender_type == "user" else "open"

        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    # =====================================================
    # ADMIN CONTROLS
    # =====================================================
    @staticmethod
    async def close_thread(
        *,
        db: AsyncSession,
        thread_id: UUID,
    ) -> ChatThread:
        """
        Admin-only: close thread permanently.
        """

        stmt = select(ChatThread).where(ChatThread.id == thread_id)
        result = await db.execute(stmt)
        thread = result.scalar_one_or_none()

        if not thread:
            raise ValueError("Chat thread not found")

        thread.is_closed = True
        thread.status = "closed"
        thread.last_message_at = datetime.utcnow()

        await db.commit()
        await db.refresh(thread)
        return thread

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user, require_admin
from app.users.models import User
from app.chat.service import ChatService
from app.chat.models import ChatThread


router = APIRouter(prefix="/chat", tags=["Chat"])


# =====================================================
# USER — GET OR CREATE THREAD
# =====================================================
@router.post("/thread")
async def get_or_create_thread(
    subject: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    thread = await ChatService.get_or_create_thread(
        db=db,
        user=current_user,
        subject=subject,
    )

    return {
        "thread_id": str(thread.id),
        "user_id": str(thread.user_id),
        "is_closed": thread.is_closed,
        "created_at": thread.created_at.isoformat(),
    }


# =====================================================
# USER — VIEW OWN THREAD
# =====================================================
@router.get("/thread/{thread_id}")
async def get_my_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    try:
        thread = await ChatService.get_thread_for_user(
            db=db,
            user=current_user,
            thread_id=thread_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "id": str(thread.id),
        "is_closed": thread.is_closed,
        "messages": [
            {
                "id": str(m.id),
                "sender_type": m.sender_type,
                "message": m.message,
                "created_at": m.created_at.isoformat(),
            }
            for m in thread.messages
        ],
    }


# =====================================================
# USER — SEND MESSAGE
# =====================================================
@router.post("/thread/{thread_id}/message")
async def send_user_message(
    thread_id: UUID,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    try:
        thread = await ChatService.get_thread_for_user(
            db=db,
            user=current_user,
            thread_id=thread_id,
        )

        msg = await ChatService.send_message(
            db=db,
            thread=thread,
            sender=current_user,
            sender_type="user",
            message=message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": str(msg.id),
        "created_at": msg.created_at.isoformat(),
    }


# =====================================================
# ADMIN — LIST ALL THREADS
# =====================================================
@router.get("/admin/threads")
async def list_all_threads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    threads = await ChatService.list_threads_for_admin(db=db)

    return [
        {
            "id": str(t.id),
            "user_id": str(t.user_id),
            "is_closed": t.is_closed,
            "created_at": t.created_at.isoformat(),
            "message_count": len(t.messages),
        }
        for t in threads
    ]


# =====================================================
# ADMIN — SEND MESSAGE
# =====================================================
@router.post("/admin/thread/{thread_id}/message")
async def send_admin_message(
    thread_id: UUID,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = await db.execute(
        select(ChatThread).where(ChatThread.id == thread_id)
    )
    thread = stmt.scalar_one_or_none()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    msg = await ChatService.send_message(
        db=db,
        thread=thread,
        sender=current_user,
        sender_type="admin",
        message=message,
    )

    return {
        "id": str(msg.id),
        "created_at": msg.created_at.isoformat(),
    }


# =====================================================
# ADMIN — CLOSE THREAD
# =====================================================
@router.post("/admin/thread/{thread_id}/close")
async def close_thread(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        thread = await ChatService.close_thread(
            db=db,
            thread_id=thread_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "closed",
        "thread_id": str(thread.id),
    }


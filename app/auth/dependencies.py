from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.core.config import settings
from app.users.models import User


async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    if settings.DEV_MODE:
        result = await db.execute(
            select(User).order_by(User.created_at.asc()).limit(1)
        )
        return result.scalar_one()

    raise HTTPException(status_code=401, detail="Authentication required")


async def require_user(
    user: User = Depends(get_current_user),
) -> User:
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

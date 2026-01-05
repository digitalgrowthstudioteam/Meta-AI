from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User


# =================================================
# 🔒 LOCKED ADMIN EMAILS (SOURCE OF TRUTH)
# =================================================
ADMIN_EMAILS = {
    "vikramrwadkar@gmail.com",
    "digitalgrowthstudioteam@gmail.com",
}


# -------------------------------------------------
# DEV-SAFE CURRENT USER RESOLUTION
# -------------------------------------------------
async def get_current_user(
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    DEV MODE:
    - Always resolve to first real user in DB
    - No env flags
    - No fake IDs
    """

    result = await db.execute(
        select(User).order_by(User.created_at.asc()).limit(1)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=500,
            detail="No user found in database",
        )

    return user


# -------------------------------------------------
# AUTH GUARDS
# -------------------------------------------------
async def require_user(
    user: User = Depends(get_current_user),
) -> User:
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    """
    🔒 ADMIN = EMAIL-BASED (HARD LOCK)
    Role column is ignored for safety.
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=403,
            detail="Admin access restricted",
        )
    return user


# -------------------------------------------------
# BACKWARD-COMPAT ALIAS (DO NOT REMOVE)
# -------------------------------------------------
require_admin_user = require_admin

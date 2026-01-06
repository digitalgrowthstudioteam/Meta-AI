from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User
from app.admin.models import GlobalSettings


# =================================================
# 🔒 LOCKED ADMIN EMAILS (SOURCE OF TRUTH)
# =================================================
ADMIN_EMAILS = {
    "vikramrwadkar@gmail.com",
    "digitalgrowthstudioteam@gmail.com",
}


# -------------------------------------------------
# INTERNAL: LOAD GLOBAL SETTINGS
# -------------------------------------------------
async def _get_global_settings(
    db: AsyncSession,
) -> GlobalSettings | None:
    result = await db.execute(
        select(GlobalSettings).limit(1)
    )
    return result.scalar_one_or_none()


# -------------------------------------------------
# BASE USER RESOLUTION (TEMP DEV MODE)
# -------------------------------------------------
async def _resolve_real_user(
    db: AsyncSession,
) -> User:
    """
    DEV MODE:
    - Always resolve to first real user in DB
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
# CURRENT USER (WITH IMPERSONATION)
# -------------------------------------------------
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_impersonate_user: str | None = Header(default=None),
) -> User:
    """
    Resolution order:
    1. Real user
    2. Admin impersonation (read-only)
    """

    real_user = await _resolve_real_user(db)

    # 🔒 MAINTENANCE MODE
    settings = await _get_global_settings(db)
    if settings and settings.maintenance_mode:
        if real_user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=503,
                detail="System under maintenance",
            )

    # -------------------------------------------------
    # 🔑 ADMIN IMPERSONATION
    # -------------------------------------------------
    if x_impersonate_user:
        if real_user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=403,
                detail="Impersonation not allowed",
            )

        stmt = select(User).where(
            (User.id == x_impersonate_user)
            | (User.email == x_impersonate_user)
        )
        result = await db.execute(stmt)
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Impersonated user not found",
            )

        # 🔒 NON-PERSISTENT FLAGS
        target_user._is_impersonated = True
        target_user._impersonated_by = real_user.email

        return target_user

    return real_user


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
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=403,
            detail="Admin access restricted",
        )
    return user


# -------------------------------------------------
# 🔒 WRITE SAFETY (IMPERSONATION)
# -------------------------------------------------
async def forbid_impersonated_writes(
    user: User = Depends(get_current_user),
) -> User:
    if getattr(user, "_is_impersonated", False):
        raise HTTPException(
            status_code=403,
            detail="Write operations disabled during impersonation",
        )
    return user


# -------------------------------------------------
# 🔁 BACKWARD-COMPAT ALIAS (CRITICAL)
# -------------------------------------------------
require_admin_user = require_admin

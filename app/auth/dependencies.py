from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User
from app.admin.models import GlobalSettings
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount


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
    result = await db.execute(select(GlobalSettings).limit(1))
    return result.scalar_one_or_none()


# -------------------------------------------------
# 🔑 REAL USER RESOLUTION (HEADER-BASED)
# -------------------------------------------------
async def _resolve_real_user(
    db: AsyncSession,
    x_user_id: str | None,
) -> User:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing user identity")

    result = await db.execute(
        select(User).where(
            (User.id == x_user_id) | (User.email == x_user_id)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user


# -------------------------------------------------
# CORE USER RESOLVER (WITH IMPERSONATION)
# -------------------------------------------------
async def _get_current_user_internal(
    db: AsyncSession,
    x_user_id: str | None,
    x_impersonate_user: str | None,
) -> User:
    real_user = await _resolve_real_user(db, x_user_id)

    # 🔒 MAINTENANCE MODE
    settings = await _get_global_settings(db)
    if settings and settings.maintenance_mode:
        if real_user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=503,
                detail="System under maintenance",
            )

    # 🔑 ADMIN IMPERSONATION
    if x_impersonate_user:
        if real_user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=403,
                detail="Impersonation not allowed",
            )

        result = await db.execute(
            select(User).where(
                (User.id == x_impersonate_user)
                | (User.email == x_impersonate_user)
            )
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Impersonated user not found",
            )

        target_user._is_impersonated = True
        target_user._impersonated_by = real_user.email
        return target_user

    return real_user


# -------------------------------------------------
# 🔐 PUBLIC DEPENDENCY: CURRENT USER
# -------------------------------------------------
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_user_id: str | None = Header(default=None),
    x_impersonate_user: str | None = Header(default=None),
) -> User:
    return await _get_current_user_internal(
        db=db,
        x_user_id=x_user_id,
        x_impersonate_user=x_impersonate_user,
    )


# -------------------------------------------------
# 🌍 SINGLE SOURCE OF TRUTH — SESSION CONTEXT
# -------------------------------------------------
async def get_session_context(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """
    GLOBAL CONTEXT:
    - Current user
    - Selected Meta ad account (ONE only)
    """

    result = await db.execute(
        select(MetaAdAccount)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.is_selected.is_(True),
        )
    )
    ad_account = result.scalar_one_or_none()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.email in ADMIN_EMAILS,
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        "ad_account": (
            {
                "id": str(ad_account.id),
                "name": ad_account.account_name,
                "meta_account_id": ad_account.meta_account_id,
            }
            if ad_account
            else None
        ),
    }


# -------------------------------------------------
# 🔒 ROLE GUARDS
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
# 🔁 BACKWARD COMPAT (DO NOT REMOVE)
# -------------------------------------------------
require_admin_user = require_admin

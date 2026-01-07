from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User
from app.admin.models import GlobalSettings
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.auth.sessions import get_active_session


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
# 🔐 COOKIE-BASED USER RESOLUTION (FINAL)
# -------------------------------------------------
async def _resolve_user_from_session(
    request: Request,
    db: AsyncSession,
) -> User:
    session_token = request.cookies.get("meta_ai_session")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await get_active_session(db, session_token=session_token)

    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    return session.user


# -------------------------------------------------
# CORE USER RESOLVER (WITH ADMIN IMPERSONATION)
# -------------------------------------------------
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user_from_session(request, db)

    # 🔒 MAINTENANCE MODE
    settings = await _get_global_settings(db)
    if settings and settings.maintenance_mode:
        if user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=503,
                detail="System under maintenance",
            )

    # 🔑 ADMIN IMPERSONATION (HEADER-BASED, OPTIONAL)
    impersonate_user = request.headers.get("X-Impersonate-User")
    if impersonate_user:
        if user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=403,
                detail="Impersonation not allowed",
            )

        result = await db.execute(
            select(User).where(
                (User.id == impersonate_user)
                | (User.email == impersonate_user)
            )
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Impersonated user not found",
            )

        target_user._is_impersonated = True
        target_user._impersonated_by = user.email
        return target_user

    return user


# -------------------------------------------------
# 🌍 GLOBAL SESSION CONTEXT (SINGLE SOURCE OF TRUTH)
# -------------------------------------------------
async def get_session_context(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
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

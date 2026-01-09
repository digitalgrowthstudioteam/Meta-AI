from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db_session import get_db
from app.users.models import User
from app.admin.models import GlobalSettings
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.auth.sessions import get_active_session
from app.campaigns.models import CampaignActionLog


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
# 🔐 COOKIE-BASED USER RESOLUTION
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

    user = session.user

    # 🔑 HARD ADMIN ROLE ASSIGNMENT
    if user.email in ADMIN_EMAILS:
        user.role = "admin"

    return user


# -------------------------------------------------
# CORE USER RESOLVER (STRICT IMPERSONATION)
# -------------------------------------------------
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user_from_session(request, db)

    settings = await _get_global_settings(db)
    if settings and settings.maintenance_mode:
        if user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=503,
                detail="System under maintenance",
            )

    # 🔁 ADMIN IMPERSONATION (STRICT + READ-ONLY)
    impersonate_user = request.headers.get("X-Impersonate-User")

    if impersonate_user:
        if user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=403,
                detail="Impersonation not allowed",
            )

        target_user_id = _safe_uuid_cast(impersonate_user)
        if not target_user_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid impersonation target",
            )

        result = await db.execute(
            select(User).where(User.id == target_user_id)
        )
        target_user = result.scalar_one_or_none()

        if not target_user:
            raise HTTPException(
                status_code=404,
                detail="Impersonated user not found",
            )

        # 🔒 HARD FLAGS — SINGLE SOURCE OF TRUTH
        target_user._is_impersonated = True
        target_user._impersonated_by = user.email
        target_user._impersonation_mode = "read_only"
        target_user._write_blocked = True

        return target_user

    # Normal user
    user._is_impersonated = False
    user._write_blocked = False
    return user


# -------------------------------------------------
# 🌍 SESSION CONTEXT (IMPERSONATION-AWARE)
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
        .where(UserMetaAdAccount.user_id == user.id)
        .order_by(MetaAdAccount.account_name)
    )

    ad_accounts = result.scalars().all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.email in ADMIN_EMAILS,
            "is_impersonated": getattr(user, "_is_impersonated", False),
            "impersonation_mode": getattr(user, "_impersonation_mode", None),
            "impersonated_by": getattr(user, "_impersonated_by", None),
            "write_blocked": getattr(user, "_write_blocked", False),
        },
        "ad_accounts": [
            {
                "id": str(acct.id),
                "name": acct.account_name,
                "meta_account_id": acct.meta_account_id,
            }
            for acct in ad_accounts
        ],
    }


# -------------------------------------------------
# SAFE UUID CAST
# -------------------------------------------------
def _safe_uuid_cast(value: str) -> UUID | None:
    try:
        return UUID(value)
    except Exception:
        return None


# -------------------------------------------------
# 🔒 GUARDS (CENTRALIZED WRITE BLOCK)
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
    if getattr(user, "_write_blocked", False):
        raise HTTPException(
            status_code=403,
            detail="Write operations disabled during impersonation",
        )
    return user


require_admin_user = require_admin

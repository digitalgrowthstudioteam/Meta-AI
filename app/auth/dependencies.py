from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.users.models import User
from app.admin.models import GlobalSettings
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.auth.sessions import get_active_session
from app.plans.subscription_models import Subscription
from app.plans.models import Plan


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
async def _get_global_settings(db: AsyncSession) -> GlobalSettings | None:
    result = await db.execute(select(GlobalSettings).limit(1))
    return result.scalar_one_or_none()


# -------------------------------------------------
# INTERNAL: LOAD ACTIVE SUBSCRIPTION (AUTO EXPIRE)
# + Extended Stripe-style metadata
# -------------------------------------------------
async def _load_active_subscription(db: AsyncSession, user: User) -> dict | None:
    now = datetime.utcnow()

    stmt = (
        select(Subscription, Plan)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.user_id == user.id)
        .where(Subscription.status.in_(["active", "trial", "grace"]))
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    res = await db.execute(stmt)
    row = res.first()

    if not row:
        return None

    sub, plan = row[0], row[1]

    # Auto-expire if ends_at passed & not never-expires
    if sub.ends_at and not sub.never_expires and sub.ends_at < now:
        sub.status = "expired"
        sub.is_active = False
        await db.commit()
        return None

    # Extended Stripe-style metadata
    in_grace = (sub.status == "grace")
    days_remaining = None
    remaining_grace_days = None
    is_expiring = False

    if sub.ends_at:
        delta = sub.ends_at - now
        days_remaining = max(delta.days, 0)
        is_expiring = (0 <= days_remaining <= 3)

    if sub.grace_ends_at:
        grace_delta = sub.grace_ends_at - now
        remaining_grace_days = max(grace_delta.days, 0)

    return {
        "id": str(sub.id),
        "status": sub.status,
        "plan_id": sub.plan_id,
        "plan_name": plan.name,
        "max_ai_campaigns": plan.max_ai_campaigns,
        "max_ad_accounts": plan.max_ad_accounts,
        "manual_allowed": plan.manual_allowed,
        "auto_allowed": plan.auto_allowed,
        "starts_at": sub.starts_at,
        "ends_at": sub.ends_at,
        "grace_ends_at": sub.grace_ends_at,
        "never_expires": sub.never_expires,

        # Stripe-style extended fields:
        "days_remaining": days_remaining,
        "remaining_grace_days": remaining_grace_days,
        "in_grace": in_grace,
        "is_expiring": is_expiring,
    }


# -------------------------------------------------
# 🔐 COOKIE-BASED USER RESOLUTION (HARD ROLE ASSIGN)
# -------------------------------------------------
async def _resolve_user_from_session(
    request: Request,
    db: AsyncSession,
) -> User:
    session_token = request.cookies.get("meta_ai_session")

    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await get_active_session(db, session_token=session_token)

    if not session or not session.user:
        raise HTTPException(status_code=401, detail="Session expired")

    user = session.user

    # 🔑 HARD ADMIN ROLE (EMAIL BASED)
    user.role = "admin" if user.email in ADMIN_EMAILS else "user"

    # Defaults
    user._is_impersonated = False
    user._write_blocked = False
    user._impersonation_mode = None
    user._impersonated_by = None

    return user


# -------------------------------------------------
# CORE USER RESOLVER (STRICT)
# -------------------------------------------------
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await _resolve_user_from_session(request, db)

    # 🔧 MAINTENANCE MODE CHECK
    settings = await _get_global_settings(db)
    if settings and settings.maintenance_mode:
        if user.email not in ADMIN_EMAILS:
            raise HTTPException(
                status_code=503,
                detail="System under maintenance",
            )

    # 🔁 ADMIN IMPERSONATION (HEADER BASED)
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

        target_user.role = "user"
        target_user._is_impersonated = True
        target_user._impersonated_by = user.email
        target_user._impersonation_mode = "read_only"
        target_user._write_blocked = True

        # No subscription enforcement in impersonation mode
        target_user._subscription = None
        return target_user

    # -------------------------------------------------
    # SUBSCRIPTION ENFORCEMENT (NON-ADMIN USERS)
    # Stripe-style grace logic (Option-C)
    # -------------------------------------------------
    sub = await _load_active_subscription(db, user)
    user._subscription = sub

    if user.role != "admin":
        if not sub:
            raise HTTPException(
                status_code=402,
                detail="No active subscription",
            )

    return user


# -------------------------------------------------
# 🌍 SESSION CONTEXT (SINGLE SOURCE OF TRUTH)
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
        "is_admin": user.role == "admin",
        "admin_view": False,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_admin": user.role == "admin",
            "is_impersonated": getattr(user, "_is_impersonated", False),
            "impersonation_mode": getattr(user, "_impersonation_mode", None),
            "impersonated_by": getattr(user, "_impersonated_by", None),
            "write_blocked": getattr(user, "_write_blocked", False),
            "subscription": user._subscription,
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
# 🔒 GUARDS
# -------------------------------------------------
async def require_user(
    user: User = Depends(get_current_user),
) -> User:
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != "admin":
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


# -------------------------------------------------
# OPTIONAL USER RESOLVER (NO THROW)
# -------------------------------------------------
async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    try:
        return await _resolve_user_from_session(request, db)
    except Exception:
        return None

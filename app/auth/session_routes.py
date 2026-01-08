"""
Session Context Routes — COOKIE MODE (NO DB is_selected)
SINGLE SOURCE OF TRUTH for frontend state

Exposes:
- GET /api/session/context
- POST /api/session/set-active

Rules:
- Uses cookie `active_account_id`
- No DB writes for switching accounts
- DB only validates ownership
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount

router = APIRouter(
    prefix="/session",
    tags=["Session Context"],
)


@router.get("/context")
async def session_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    GLOBAL SESSION CONTEXT
    Returns:
    - Authenticated user
    - List of ALL linked Meta ad accounts
    - Active ad account via cookie
    """

    # Load all linked ad accounts
    result = await db.execute(
        select(
            MetaAdAccount.id,
            MetaAdAccount.account_name,
            MetaAdAccount.meta_account_id,
        )
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(UserMetaAdAccount.user_id == user.id)
        .order_by(MetaAdAccount.account_name)
    )

    rows = result.all()

    ad_accounts = [
        {
            "id": str(r.id),
            "name": r.account_name,
            "meta_account_id": r.meta_account_id,
        }
        for r in rows
    ]

    # Read active from cookie
    cookie_active_id = request.cookies.get("active_account_id")

    # Validate cookie belongs to current user
    active = next((a for a in ad_accounts if a["id"] == cookie_active_id), None)

    # Fallback to first account if invalid or not set
    if not active and ad_accounts:
        active = ad_accounts[0]
        cookie_active_id = active["id"]

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.role == "admin",
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        "ad_accounts": ad_accounts,
        "active_ad_account_id": cookie_active_id,
        "ad_account": active,  # backward compatibility
    }


@router.post("/set-active")
async def set_active_ad_account(
    payload: dict,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Switch active account using a cookie (NO DB writes)
    Body: { "account_id": "<uuid>" }
    """

    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id required")

    # Validate account belongs to this user
    result = await db.execute(
        select(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.meta_ad_account_id == account_id,
        )
    )
    relation = result.scalar_one_or_none()

    if not relation:
        raise HTTPException(status_code=403, detail="Not authorized to use this account")

    # Write cookie for frontend
    response.set_cookie(
        key="active_account_id",
        value=account_id,
        httponly=False,   # FE needs access
        samesite="Lax",
        path="/",
    )

    return {"status": "ok", "active_account_id": account_id}

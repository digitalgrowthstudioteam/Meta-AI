"""
Session Context Routes — COOKIE MODE (NO DB writes)
SINGLE SOURCE OF TRUTH for frontend state

Exposes:
- GET /api/session/context
- POST /api/session/set-active

Rules:
- Uses cookies only
- No DB writes for switching views/accounts
- DB only validates ownership
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user_optional
from app.users.models import User
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount

# ----------------------------------------
# Support both /session/* and /api/session/*
# ----------------------------------------
router = APIRouter(prefix="/session", tags=["Session Context"])
api_router = APIRouter(prefix="/api/session", tags=["Session Context"])


@router.get("/context")
@api_router.get("/context")
async def session_context(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    """
    GLOBAL SESSION CONTEXT
    """

    # If user not logged in → return safe JSON (avoid redirect loops)
    if not user:
        return {
            "is_logged_in": False,
            "is_admin": False,
            "admin_view": False,
            "ad_accounts": [],
            "active_ad_account_id": None,
            "ad_account": None,
            "user": None,
        }

    # -----------------------------
    # ADMIN / USER VIEW MODE
    # -----------------------------
    is_admin = user.role == "admin"
    admin_view_cookie = request.cookies.get("admin_view") == "true"
    admin_view = bool(is_admin and admin_view_cookie)

    # 🔒 Always set role cookie (middleware depends on it)
    response.set_cookie(
        key="meta_ai_role",
        value="admin" if is_admin else "user",
        httponly=False,
        samesite="Lax",
        path="/",
    )

    # -----------------------------
    # LOAD AD ACCOUNTS (USER MODE)
    # -----------------------------
    ad_accounts = []
    active_account = None
    active_account_id = None

    if not admin_view:
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

        cookie_active_id = request.cookies.get("active_account_id")
        active_account = next(
            (a for a in ad_accounts if a["id"] == cookie_active_id),
            None,
        )

        if not active_account and ad_accounts:
            active_account = ad_accounts[0]
            active_account_id = active_account["id"]
        else:
            active_account_id = cookie_active_id

    # -----------------------------
    # RESPONSE
    # -----------------------------
    return {
        "is_logged_in": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "is_admin": is_admin,
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        "is_admin": is_admin,
        "admin_view": admin_view,
        "ad_accounts": ad_accounts,
        "active_ad_account_id": active_account_id,
        "ad_account": active_account,  # backward compatibility
    }


@router.post("/set-active")
@api_router.post("/set-active")
async def set_active_ad_account(
    payload: dict,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_optional),
):
    """
    Switch active account using cookie (NO DB writes)
    """

    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")

    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id required")

    result = await db.execute(
        select(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.meta_ad_account_id == account_id,
        )
    )

    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized")

    response.set_cookie(
        key="active_account_id",
        value=account_id,
        httponly=False,
        samesite="Lax",
        path="/",
    )

    return {"status": "ok"}

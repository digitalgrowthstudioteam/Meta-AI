"""
Auth Routes
- /auth/login
- /auth/verify
- /auth/logout
- /auth/me
- /session/context   ✅ SINGLE SOURCE OF TRUTH
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.service import request_magic_login, verify_magic_login
from app.auth.dependencies import (
    require_user,
    get_session_context,
)
from app.users.models import User

router = APIRouter(tags=["auth"])


# =========================================================
# REQUEST MAGIC LINK (JSON BODY)
# =========================================================
@router.post("/auth/login")
async def login_request(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email required",
        )

    sent = await request_magic_login(db, email=email)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send login link",
        )

    return {"ok": True}


# =========================================================
# VERIFY MAGIC LINK (SET COOKIES + REDIRECT)
# =========================================================
@router.get("/auth/verify")
async def verify_login(
    token: str = Query(...),
    next: str = Query("/dashboard"),
    db: AsyncSession = Depends(get_db),
):
    session_token = await verify_magic_login(db, raw_token=token)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login link",
        )

    # 🔐 Resolve user to determine role
    user = await require_user(
        request=None,  # not used inside dependency
        db=db,
    )

    response = RedirectResponse(
        url=next,
        status_code=status.HTTP_302_FOUND,
    )

    # 🔑 SESSION COOKIE
    response.set_cookie(
        key="meta_ai_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60 * 60 * 24 * 3,  # 3 days
    )

    # 🔒 ROLE COOKIE (CRITICAL FOR MIDDLEWARE)
    response.set_cookie(
        key="meta_ai_role",
        value=user.role,          # "admin" | "user"
        httponly=False,           # middleware must read
        secure=True,
        samesite="none",
        path="/",
        max_age=60 * 60 * 24 * 3,
    )

    return response


# =========================================================
# AUTH SESSION CHECK
# =========================================================
@router.get("/auth/me")
async def auth_me(
    user: User = Depends(require_user),
):
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


# =========================================================
# LOGOUT
# =========================================================
@router.post("/auth/logout")
async def logout(
    _: User = Depends(require_user),
):
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND,
    )

    response.delete_cookie(key="meta_ai_session", path="/")
    response.delete_cookie(key="meta_ai_role", path="/")

    return response


# =========================================================
# 🌍 GLOBAL SESSION CONTEXT (SINGLE ENDPOINT)
# =========================================================
@router.get("/session/context")
async def session_context(
    context: dict = Depends(get_session_context),
):
    return context

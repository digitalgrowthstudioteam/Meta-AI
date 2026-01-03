"""
Auth Routes
- /auth/login
- /auth/verify
- /auth/logout
- /auth/me
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.service import request_magic_login, verify_magic_login
from app.auth.dependencies import require_user
from app.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# =========================================================
# REQUEST MAGIC LINK
# =========================================================
@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login_request(
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    await request_magic_login(db, email=email)
    return None


# =========================================================
# VERIFY MAGIC LINK (SET COOKIE + REDIRECT → NEXT.JS)
# =========================================================
@router.get("/verify")
async def verify_login(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    session_token = await verify_magic_login(db, raw_token=token)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login link",
        )

    response = RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_302_FOUND,
    )

    # 🔐 AUTH COOKIE — MAGIC LINK SAFE CONFIG
    response.set_cookie(
        key="meta_ai_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",   # ✅ CRITICAL FIX
        path="/",
        max_age=60 * 60 * 24 * 3,  # 3 days
    )

    return response


# =========================================================
# AUTH SESSION CHECK (USED BY NEXT.JS)
# =========================================================
@router.get("/me")
async def auth_me(
    user: User = Depends(require_user),
):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }


# =========================================================
# LOGOUT
# =========================================================
@router.post("/logout")
async def logout(
    _: User = Depends(require_user),
):
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND,
    )

    response.delete_cookie(
        key="meta_ai_session",
        path="/",
    )

    return response

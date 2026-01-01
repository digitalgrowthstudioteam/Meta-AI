"""
Auth Routes
- /auth/login
- /auth/verify
- /auth/logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.service import request_magic_login, verify_magic_login
from app.auth.sessions import revoke_session
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
# VERIFY MAGIC LINK (SET COOKIE + REDIRECT)
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

    # 🔐 Secure, HTTP-only cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,          # HTTPS only
        samesite="lax",
        max_age=60 * 60 * 24 * 3,  # 3 days
    )

    return response


# =========================================================
# LOGOUT
# =========================================================
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    # Cookie-based logout
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_302_FOUND,
    )

    response.delete_cookie("session_token")

    return response

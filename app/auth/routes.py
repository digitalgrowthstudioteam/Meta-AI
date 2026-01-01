"""
Auth Routes
- /auth/login
- /auth/verify
- /auth/logout

Rules:
- Thin routes ONLY
- No business logic
- Delegate to service / sessions layers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.service import request_magic_login, verify_magic_login
from app.auth.sessions import revoke_session
from app.auth.dependencies import require_user
from app.users.models import User


router = APIRouter(prefix="/auth", tags=["auth"])


# =========================================================
# REQUEST MAGIC LINK (HTML FORM SAFE)
# =========================================================
@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login_request(
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Request a magic login link.
    Always returns 204 to avoid email enumeration.
    """
    await request_magic_login(db, email=email)
    return None


# =========================================================
# VERIFY MAGIC LINK
# =========================================================
@router.get("/verify")
async def verify_login(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify magic token and create session.
    Returns session token for client usage.
    """
    session_token = await verify_magic_login(db, raw_token=token)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired login link",
        )

    return {
        "session_token": session_token,
        "token_type": "Bearer",
    }


# =========================================================
# LOGOUT
# =========================================================
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(require_user),
    authorization: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout current session.
    Requires Authorization: Bearer <session_token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization header missing",
        )

    session_token = authorization.replace("Bearer ", "").strip()
    await revoke_session(db, session_token=session_token)
    return None

"""
Authentication Dependencies
- Resolve current user from session token
- Enforce user / admin access

Rules:
- Server-side session validation ONLY
- Support Authorization header (API)
- Support HTTP-only cookie (Browser UI)
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.sessions import get_active_session
from app.users.models import User


# =========================================================
# CURRENT USER DEPENDENCY (HEADER OR COOKIE)
# =========================================================
async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    meta_ai_session: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve current logged-in user from session token.

    Priority:
    1. Authorization header (API clients)
    2. HTTP-only cookie (Browser UI)
    """

    token: Optional[str] = None

    # -------------------------------
    # API Clients (Authorization)
    # -------------------------------
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format",
            )
        token = authorization.replace("Bearer ", "").strip()

    # -------------------------------
    # Browser UI (Cookie)
    # -------------------------------
    elif meta_ai_session:
        token = meta_ai_session

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    session = await get_active_session(db, token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive or not found",
        )

    return user


# =========================================================
# USER-ONLY ACCESS
# =========================================================
async def require_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


# =========================================================
# ADMIN-ONLY ACCESS
# =========================================================
async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

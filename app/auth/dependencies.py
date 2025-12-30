"""
Authentication Dependencies
- Resolve current user from session token
- Enforce user / admin access

Rules:
- Server-side session validation ONLY
- No cookies assumption yet
- Session token expected via Authorization header
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.sessions import get_active_session
from app.users.models import User


# =========================================================
# CURRENT USER DEPENDENCY
# =========================================================
async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve current logged-in user from session token.
    Expects:
    Authorization: Bearer <session_token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format",
        )

    session_token = authorization.replace("Bearer ", "").strip()

    session = await get_active_session(db, session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = session.user
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
    """
    Ensure user is authenticated (any role).
    """
    return current_user


# =========================================================
# ADMIN-ONLY ACCESS
# =========================================================
async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure user has admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

"""
Session Management Logic
- Create session
- Validate session
- Expire session
- Logout (soft revoke)

Rules:
- Server-side sessions ONLY
- Session expiry: 3 days (LOCKED)
- No routing
- No magic link logic
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.auth.models import Session
from app.users.models import User

# =========================================================
# CONSTANTS (LOCKED)
# =========================================================
SESSION_EXPIRE_DAYS = 3


# =========================================================
# SESSION TOKEN GENERATION
# =========================================================
def generate_session_token() -> str:
    """
    Generate a secure session token.
    Stored server-side only.
    """
    return secrets.token_urlsafe(48)


def session_expiry() -> datetime:
    """
    Returns session expiry datetime (UTC).
    """
    return datetime.now(timezone.utc) + timedelta(days=SESSION_EXPIRE_DAYS)


# =========================================================
# SESSION CREATION
# =========================================================
async def create_session(
    db: AsyncSession,
    user: User,
) -> Session:
    """
    Create a new active session for a user.
    """
    token = generate_session_token()

    session = Session(
        user_id=user.id,
        session_token=token,
        expires_at=session_expiry(),
        is_active=True,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


# =========================================================
# SESSION VALIDATION
# =========================================================
async def get_active_session(
    db: AsyncSession,
    session_token: str,
) -> Optional[Session]:
    """
    Fetch a valid active session.
    """
    result = await db.execute(
        select(Session).where(
            Session.session_token == session_token,
            Session.is_active.is_(True),
            Session.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


# =========================================================
# SESSION REVOCATION
# =========================================================
async def revoke_session(
    db: AsyncSession,
    session_token: str,
) -> None:
    """
    Soft revoke a session (logout).
    """
    await db.execute(
        update(Session)
        .where(Session.session_token == session_token)
        .values(is_active=False)
    )
    await db.commit()


async def revoke_all_sessions_for_user(
    db: AsyncSession,
    user_id,
) -> None:
    """
    Revoke all active sessions for a user.
    Used for admin kill-switch later.
    """
    await db.execute(
        update(Session)
        .where(
            Session.user_id == user_id,
            Session.is_active.is_(True),
        )
        .values(is_active=False)
    )
    await db.commit()

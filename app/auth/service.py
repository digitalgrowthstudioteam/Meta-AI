"""
Authentication Service (Orchestrator)

Responsibilities:
- Handle magic link login request
- Verify magic link token
- Auto-create user on first login
- Create server-side session
- Enforce IST-based unique email subject

Rules:
- NO routes here
- NO real email sending
- NO billing enforcement
- NO Meta / AI logic
"""

from app.core.email import send_email
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.models import MagicLoginToken
from app.auth.tokens import (
    create_magic_token_pair,
    magic_token_expiry,
    hash_magic_token,
    is_token_expired,
)
from app.auth.sessions import create_session
from app.users.models import User


# =========================================================
# CONSTANTS (LOCKED)
# =========================================================
IST_ZONE = ZoneInfo("Asia/Kolkata")


# =========================================================
# EMAIL SUBJECT (LOCKED FORMAT)
# =========================================================
def build_magic_link_subject() -> str:
    """
    Build unique email subject with IST timestamp.
    Example:
    Digital Growth Studio Login | 30 Dec 2025, 18:45 IST
    """
    now_ist = datetime.now(IST_ZONE)
    return (
        f"Digital Growth Studio Login | "
        f"{now_ist.strftime('%d %b %Y, %H:%M')} IST"
    )


# =========================================================
# PLACEHOLDER EMAIL SENDER (NO-OP)
# =========================================================
def send_magic_link_email(
    to_email: str,
    magic_link: str,
    subject: str,
) -> None:
    """
    Send magic login link via SMTP.
    """
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Digital Growth Studio</h2>
            <p>Click the button below to log in:</p>
            <p>
                <a href="{magic_link}"
                   style="padding:12px 18px;
                          background:#4F46E5;
                          color:#ffffff;
                          text-decoration:none;
                          border-radius:6px;">
                    Login to Dashboard
                </a>
            </p>
            <p>This link expires in 10 minutes.</p>
            <p>If you did not request this, ignore this email.</p>
        </body>
    </html>
    """

    send_email(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=f"Login link: {magic_link}",
    )

# =========================================================
# LOGIN REQUEST FLOW
# =========================================================
async def request_magic_login(
    db: AsyncSession,
    email: str,
) -> None:
    """
    Step 1:
    - Generate magic token
    - Store hashed token
    - Send placeholder email
    """
    raw_token, token_hash = create_magic_token_pair()

    magic_token = MagicLoginToken(
        email=email,
        token_hash=token_hash,
        expires_at=magic_token_expiry(),
        is_used=False,
    )

    db.add(magic_token)
    await db.commit()

    subject = build_magic_link_subject()

    # Magic link format (frontend will consume later)
    magic_link = f"/auth/verify?token={raw_token}"

    send_magic_link_email(
        to_email=email,
        magic_link=magic_link,
        subject=subject,
    )


# =========================================================
# TOKEN VERIFICATION FLOW
# =========================================================
async def verify_magic_login(
    db: AsyncSession,
    raw_token: str,
) -> Optional[str]:
    """
    Step 2:
    - Verify magic token
    - Mark token as used
    - Create or fetch user
    - Create session
    - Return session token
    """
    token_hash = hash_magic_token(raw_token)

    result = await db.execute(
        select(MagicLoginToken).where(
            MagicLoginToken.token_hash == token_hash,
            MagicLoginToken.is_used.is_(False),
        )
    )
    magic_token = result.scalar_one_or_none()

    if not magic_token:
        return None

    if is_token_expired(magic_token.expires_at):
        return None

    # Mark token as used
    magic_token.is_used = True
    magic_token.used_at = datetime.utcnow()
    await db.commit()

    # Fetch or create user
    user = await _get_or_create_user(db, magic_token.email)

    # Create session
    session = await create_session(db, user)

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    await db.commit()

    return session.session_token


# =========================================================
# INTERNAL HELPERS
# =========================================================
async def _get_or_create_user(
    db: AsyncSession,
    email: str,
) -> User:
    """
    Fetch existing user or auto-create new user.
    Trial assignment hook lives here (future).
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user:
        return user

    # Auto-create user (trial assignment happens later)
    user = User(
        email=email,
        name=email.split("@")[0],
        role="user",
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

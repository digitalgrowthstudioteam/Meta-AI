"""
Authentication Service (Orchestrator)

Responsibilities:
- Handle magic link login request
- Verify magic link token
- Auto-create user on first login
- Create server-side session

IMPORTANT (LOCKED DESIGN):
- Trial subscription assignment is INTENTIONALLY DISABLED
- Plan & billing logic will be re-enabled in Phase 5
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.email import send_email
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

MAX_ACTIVE_TOKENS_PER_EMAIL = 3
TOKEN_COOLDOWN_MINUTES = 2


# =========================================================
# EMAIL SUBJECT
# =========================================================
def build_magic_link_subject() -> str:
    now_ist = datetime.now(IST_ZONE)
    return (
        f"Digital Growth Studio Login | "
        f"{now_ist.strftime('%d %b %Y, %H:%M')} IST"
    )


# =========================================================
# EMAIL SENDER
# =========================================================
def send_magic_link_email(
    to_email: str,
    magic_link: str,
    subject: str,
) -> None:
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
# LOGIN REQUEST FLOW (FIXED)
# =========================================================
async def request_magic_login(
    db: AsyncSession,
    email: str,
) -> bool:
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=TOKEN_COOLDOWN_MINUTES)

    # 🔥 Remove expired or old unused tokens
    await db.execute(
        delete(MagicLoginToken).where(
            MagicLoginToken.email == email,
            MagicLoginToken.is_used.is_(False),
            MagicLoginToken.created_at < cutoff,
        )
    )
    await db.commit()

    # 🔒 Count ONLY recent tokens (cooldown window)
    result = await db.execute(
        select(MagicLoginToken).where(
            MagicLoginToken.email == email,
            MagicLoginToken.is_used.is_(False),
            MagicLoginToken.created_at >= cutoff,
        )
    )
    recent_tokens = result.scalars().all()

    if len(recent_tokens) >= MAX_ACTIVE_TOKENS_PER_EMAIL:
        return False

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

    base_url = settings.PUBLIC_APP_URL.rstrip("/")
    magic_link = f"{base_url}/api/auth/verify?token={raw_token}"

    send_magic_link_email(
        to_email=email,
        magic_link=magic_link,
        subject=subject,
    )

    return True


# =========================================================
# TOKEN VERIFICATION FLOW
# (UPDATED: RETURNS (session_token, user))
# =========================================================
async def verify_magic_login(
    db: AsyncSession,
    raw_token: str,
) -> Optional[Tuple[str, User]]:
    token_hash = hash_magic_token(raw_token)

    result = await db.execute(
        select(MagicLoginToken).where(
            MagicLoginToken.token_hash == token_hash,
            MagicLoginToken.is_used.is_(False),
        )
    )
    magic_token = result.scalar_one_or_none()

    if not magic_token or is_token_expired(magic_token.expires_at):
        return None

    magic_token.is_used = True
    magic_token.used_at = datetime.utcnow()
    await db.commit()

    user = await _get_or_create_user(db, magic_token.email)
    session = await create_session(db, user)

    user.last_login_at = datetime.utcnow()
    await db.commit()

    return session.session_token, user


# =========================================================
# INTERNAL HELPERS
# =========================================================
async def _get_or_create_user(
    db: AsyncSession,
    email: str,
) -> User:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user:
        return user

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

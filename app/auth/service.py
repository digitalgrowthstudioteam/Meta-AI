"""
Authentication Service (Orchestrator)

Responsibilities:
- Handle magic link login request
- Verify magic link token
- Auto-create user on first login
- Create server-side session
- Assign trial subscription on first successful login

Rules:
- NO routes here
- NO billing enforcement
- NO Meta / AI logic
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from app.plans.subscription_models import Subscription


# =========================================================
# CONSTANTS (LOCKED)
# =========================================================
IST_ZONE = ZoneInfo("Asia/Kolkata")
TRIAL_DAYS = 7
GRACE_DAYS = 3
TRIAL_AI_LIMIT = 3


# =========================================================
# EMAIL SUBJECT (LOCKED FORMAT)
# =========================================================
def build_magic_link_subject() -> str:
    """
    Build unique email subject with IST timestamp.
    """
    now_ist = datetime.now(IST_ZONE)
    return (
        f"Digital Growth Studio Login | "
        f"{now_ist.strftime('%d %b %Y, %H:%M')} IST"
    )


# =========================================================
# PLACEHOLDER EMAIL SENDER
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
# LOGIN REQUEST FLOW
# =========================================================
async def request_magic_login(
    db: AsyncSession,
    email: str,
) -> None:
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
    magic_link = f"https://meta-ai.digitalgrowthstudio.in/auth/verify?token={raw_token}"

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

    # Mark token as used
    magic_token.is_used = True
    magic_token.used_at = datetime.utcnow()
    await db.commit()

    # Fetch or create user
    user = await _get_or_create_user(db, magic_token.email)

    # Assign trial if needed
    await _assign_trial_if_needed(db, user)

    # Create session
    session = await create_session(db, user)

    # Update last login
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


async def _assign_trial_if_needed(
    db: AsyncSession,
    user: User,
) -> None:
    """
    Assign 7-day trial + 3-day grace period
    ONLY if user has no subscription.
    """
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id
        )
    )
    existing = result.scalars().first()

    if existing:
        return

    now = datetime.utcnow()
    trial_end = now + timedelta(days=TRIAL_DAYS)
    grace_end = trial_end + timedelta(days=GRACE_DAYS)

    subscription = Subscription(
        user_id=user.id,
        is_trial=True,
        trial_start_date=now.date(),
        trial_end_date=trial_end.date(),
        status="trial",
        starts_at=now,
        ends_at=trial_end,
        grace_ends_at=grace_end,
        ai_campaign_limit_snapshot=TRIAL_AI_LIMIT,
        is_active=True,
        created_by_admin=False,
        assigned_by_admin=False,
    )

    db.add(subscription)
    await db.flush()   # IMPORTANT: force DB write
    await db.commit()

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db

# AUTH IS TEMPORARILY DISABLED (DEV MODE)
# get_current_user WILL BE REINTRODUCED LATER VIA NEXT.JS
from app.users.models import User

from app.meta_api.models import (
    MetaOAuthToken,
    UserMetaAdAccount,
    MetaAdAccount,
)
from app.campaigns.models import Campaign


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# --------------------------------------------------
# DEV MODE USER RESOLUTION (TEMPORARY)
# --------------------------------------------------
async def get_dev_user(db: AsyncSession) -> Optional[User]:
    """
    Temporary user resolver while auth is disabled.
    Uses first available user in database.

    THIS WILL BE REMOVED when auth middleware is enabled.
    """
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none()


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard Summary (READ-ONLY)

    FINAL CONTRACT — DO NOT CHANGE SHAPE

    Auth: Disabled (Development Mode)
    """

    # --------------------------------------------------
    # Resolve user (DEV MODE)
    # --------------------------------------------------
    current_user = await get_dev_user(db)

    if not current_user:
        # No users exist yet — return empty safe dashboard
        return {
            "meta_connected": False,
            "ad_accounts": 0,
            "campaigns": {
                "total": 0,
                "ai_active": 0,
                "ai_limit": 0,
            },
            "ai": {
                "engine_status": "off",
                "last_action_at": None,
            },
            "subscription": {
                "plan": "none",
                "expires_at": None,
                "manual_campaign_credits": 0,
            },
        }

    # --------------------------------------------------
    # 1. Meta connection status
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(MetaOAuthToken)
        .where(
            MetaOAuthToken.user_id == current_user.id,
            MetaOAuthToken.is_active.is_(True),
        )
    )
    meta_connected = (result.scalar() or 0) > 0

    # --------------------------------------------------
    # 2. Ad accounts count
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == current_user.id)
    )
    ad_accounts = result.scalar() or 0

    # --------------------------------------------------
    # 3. Campaign count
    # campaigns → meta_ad_accounts → user_meta_ad_accounts → user
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(Campaign)
        .join(
            MetaAdAccount,
            Campaign.ad_account_id == MetaAdAccount.id,
        )
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == current_user.id,
            Campaign.is_archived.is_(False),
        )
    )
    total_campaigns = result.scalar() or 0

    # --------------------------------------------------
    # 4. AI rules (Phase 1)
    # --------------------------------------------------
    ai_active = 0
    ai_limit = 3  # TEMP: will come from subscription later

    # --------------------------------------------------
    # FINAL RESPONSE (LOCKED)
    # --------------------------------------------------
    return {
        "meta_connected": meta_connected,
        "ad_accounts": ad_accounts,
        "campaigns": {
            "total": total_campaigns,
            "ai_active": ai_active,
            "ai_limit": ai_limit,
        },
        "ai": {
            "engine_status": "off",
            "last_action_at": None,
        },
        "subscription": {
            "plan": "starter",
            "expires_at": None,
            "manual_campaign_credits": 0,
        },
    }

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
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


@router.get("/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard Summary (READ-ONLY)
    FINAL CONTRACT — DO NOT CHANGE SHAPE
    """

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
    # 3. Total campaigns
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
    # 4. AI-ACTIVE campaigns
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
            Campaign.ai_active.is_(True),
        )
    )
    ai_active = result.scalar() or 0

    ai_limit = 3  # phase-1 temp

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

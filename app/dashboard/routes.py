from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import get_session_context
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
    session: dict = Depends(get_session_context),
):
    """
    Dashboard Summary (READ-ONLY)
    STRICT — SESSION CONTEXT ONLY
    """

    user_id = session["user"]["id"]
    ad_account = session["ad_account"]

    # --------------------------------------------------
    # 1. Meta connection status
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(MetaOAuthToken)
        .where(
            MetaOAuthToken.user_id == user_id,
            MetaOAuthToken.is_active.is_(True),
        )
    )
    meta_connected = (result.scalar() or 0) > 0

    # --------------------------------------------------
    # 2. Ad accounts count (user-scoped)
    # --------------------------------------------------
    result = await db.execute(
        select(func.count())
        .select_from(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == user_id)
    )
    ad_accounts = result.scalar() or 0

    # --------------------------------------------------
    # 3. Campaigns (STRICT SELECTED ACCOUNT)
    # --------------------------------------------------
    total_campaigns = 0
    ai_active = 0

    if ad_account:
        # total campaigns
        result = await db.execute(
            select(func.count())
            .select_from(Campaign)
            .where(
                Campaign.ad_account_id == ad_account["id"],
                Campaign.is_archived.is_(False),
            )
        )
        total_campaigns = result.scalar() or 0

        # ai-active campaigns
        result = await db.execute(
            select(func.count())
            .select_from(Campaign)
            .where(
                Campaign.ad_account_id == ad_account["id"],
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

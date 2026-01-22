from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.meta_api.models import UserMetaAdAccount
from app.campaigns.models import Campaign
from app.plans.subscription_models import Subscription

router = APIRouter(prefix="/usage", tags=["Usage Summary"])


@router.get(
    "/summary",
    status_code=status.HTTP_200_OK,
)
async def usage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Unified Phase-9 Usage Summary (User-Side)
    """
    # -------------------------
    # Fetch active subscription
    # -------------------------
    sub = await db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["trial", "active"])
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )

    # -------------------------
    # If no subscription exists
    # -------------------------
    if not sub:
        return {
            "ad_accounts": {"used": 0, "limit": 0},
            "campaigns": {"used": 0, "limit": 0},
            "ai_campaigns": {"used": 0, "limit": 0},
        }

    # -------------------------
    # Ad Account usage
    # -------------------------
    ad_accounts_used = await db.scalar(
        select(func.count(UserMetaAdAccount.id)).where(
            UserMetaAdAccount.user_id == current_user.id
        )
    ) or 0

    ad_account_limit = sub.ad_account_limit_snapshot or 0

    # -------------------------
    # Campaign usage
    # -------------------------
    campaigns_used = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.user_id == current_user.id,
            Campaign.is_archived.is_(False),
        )
    ) or 0

    campaign_limit = sub.campaign_limit_snapshot or 0

    # -------------------------
    # AI Campaign usage
    # -------------------------
    ai_campaigns_used = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.user_id == current_user.id,
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
        )
    ) or 0

    ai_campaign_limit = sub.ai_campaign_limit_snapshot or 0

    # -------------------------
    # Optional future advanced slots
    # -------------------------
    # e.g., expansions, optimizations per day/month can be plugged here

    return {
        "ad_accounts": {
            "used": ad_accounts_used,
            "limit": ad_account_limit
        },
        "campaigns": {
            "used": campaigns_used,
            "limit": campaign_limit
        },
        "ai_campaigns": {
            "used": ai_campaigns_used,
            "limit": ai_campaign_limit
        },
    }

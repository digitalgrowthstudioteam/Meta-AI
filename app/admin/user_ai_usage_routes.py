from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign
from app.plans.subscription_models import Subscription, SubscriptionAddon

router = APIRouter(prefix="/admin/users", tags=["Admin User AI Usage"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/{user_id}/ai-usage")
async def user_ai_usage(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    campaigns = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == user_id, Campaign.ai_active.is_(True))
    )

    campaign_list = campaigns.scalars().all()

    total_active = len(campaign_list)
    campaign_details = [
        {
            "id": str(c.id),
            "name": c.name,
            "objective": c.objective,
            "status": c.status,
            "ai_activated_at": c.ai_activated_at.isoformat()
            if c.ai_activated_at
            else None,
        }
        for c in campaign_list
    ]

    subscription = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )

    addons = await db.execute(
        select(SubscriptionAddon).where(SubscriptionAddon.user_id == user_id)
    )

    total_slots = (subscription.ai_campaign_limit_snapshot if subscription else 0) + sum(
        a.extra_ai_campaigns for a in addons.scalars().all()
    )

    return {
        "total_active_ai_campaigns": total_active,
        "total_slots": total_slots,
        "campaigns": campaign_details,
    }

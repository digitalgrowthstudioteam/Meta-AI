from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.models.action_models import AIAction
from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount


router = APIRouter(
    prefix="/ai",
    tags=["AI Suggestions"],
)


# =====================================================
# LIST AI SUGGESTIONS (READ-ONLY — PERSISTED)
# =====================================================
@router.get("/actions", response_model=List[AIAction])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
    limit: int = 50,
):
    """
    Returns persisted AI suggestions for the logged-in user.

    Phase 7 rules:
    - READ ONLY
    - No AI execution
    - No Meta mutation
    - Deterministic & explainable
    """

    stmt = (
        select(AIAction)
        .join(Campaign, Campaign.id == AIAction.campaign_id)
        .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == user.id,
        )
        .order_by(desc(AIAction.created_at))
        .limit(limit)
    )

    result = await db.execute(stmt)
    return result.scalars().all()


# =====================================================
# AI ACTION HISTORY FOR A CAMPAIGN
# =====================================================
@router.get("/campaign/{campaign_id}/actions", response_model=List[AIAction])
async def list_campaign_ai_actions(
    *,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Returns AI action history for a specific campaign.
    """

    stmt = (
        select(AIAction)
        .join(Campaign, Campaign.id == AIAction.campaign_id)
        .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            Campaign.id == campaign_id,
            UserMetaAdAccount.user_id == user.id,
        )
        .order_by(desc(AIAction.created_at))
    )

    result = await db.execute(stmt)
    return result.scalars().all()

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
# LIST AI SUGGESTIONS (READ-ONLY)
# =====================================================
@router.get("/actions", response_model=None)
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
    limit: int = 50,
) -> List[AIAction]:
    """
    Returns AI suggestions visible to the logged-in user.

    Includes:
    - Suggested actions
    - Explainability payload
    - Confidence level
    - Status lifecycle

    Read-only endpoint.
    """

    stmt = (
        select(AIAction)
        .join(
            Campaign,
            Campaign.id == AIAction.campaign_id,
        )
        .join(
            MetaAdAccount,
            Campaign.ad_account_id == MetaAdAccount.id,
        )
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
    actions = result.scalars().all()

    return actions


# =====================================================
# AI ACTION HISTORY FOR A CAMPAIGN
# =====================================================
@router.get("/campaign/{campaign_id}/actions", response_model=None)
async def list_campaign_ai_actions(
    *,
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
) -> List[AIAction]:
    """
    Returns full AI action history for a specific campaign.

    Read-only.
    """

    stmt = (
        select(AIAction)
        .join(
            Campaign,
            Campaign.id == AIAction.campaign_id,
        )
        .join(
            MetaAdAccount,
            Campaign.ad_account_id == MetaAdAccount.id,
        )
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
    actions = result.scalars().all()

    return actions

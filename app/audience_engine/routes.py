from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign
from app.audience_engine.service import AudienceIntelligenceService


router = APIRouter(prefix="/audience", tags=["Audience Intelligence"])


# =====================================================
# LIST AUDIENCE INSIGHTS FOR A CAMPAIGN
# =====================================================
@router.get("/campaign/{campaign_id}/insights")
async def list_campaign_audience_insights(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    campaign = await db.get(Campaign, campaign_id)

    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    insights = await AudienceIntelligenceService.list_insights_for_campaign(
        db=db,
        campaign_id=campaign_id,
        limit=10,
    )

    return [
        {
            "id": str(i.id),
            "suggestion_type": i.suggestion_type,
            "reason": i.reason,
            "confidence_score": i.confidence_score,
            "fatigue_score": i.fatigue_score,
            "conversion_lift": i.conversion_lift,
            "audience_size_delta": i.audience_size_delta,
            "source": i.source,
            "created_at": i.created_at.isoformat(),
        }
        for i in insights
    ]

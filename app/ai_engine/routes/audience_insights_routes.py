"""
Audience Insights Routes

PHASE 8 — READ-ONLY AI AUDIENCE INSIGHTS API

Purpose:
- Expose audience insights to frontend
- NO Meta mutation
- NO DB writes
"""

from uuid import UUID
from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.ai_engine.services.audience_insights_service import (
    AudienceInsightsService,
)

router = APIRouter(
    prefix="/ai/audience-insights",
    tags=["AI Audience Insights"],
)


# =====================================================
# GET AUDIENCE INSIGHTS FOR A CAMPAIGN
# =====================================================
@router.get("/{campaign_id}")
async def get_audience_insights(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Returns READ-ONLY audience insights for a campaign.
    """

    insights = await AudienceInsightsService.generate_insights(
        db=db,
        campaign_id=campaign_id,
    )

    return {
        "campaign_id": campaign_id,
        "insights": insights,
    }

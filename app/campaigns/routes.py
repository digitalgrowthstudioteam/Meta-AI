from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaigns = await CampaignService.list_campaigns(
        db=db,
        user_id=current_user.id,
    )
    return campaigns


@router.post("/{campaign_id}/ai-toggle", response_model=CampaignResponse)
async def toggle_ai(
    campaign_id: UUID,
    payload: ToggleAIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        campaign = await CampaignService.toggle_ai(
            db=db,
            user_id=current_user.id,
            campaign_id=campaign_id,
            enable=payload.enable,
        )
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

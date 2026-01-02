from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# LIST CAMPAIGNS (READ-ONLY VISIBILITY)
# =========================================================
@router.get(
    "/",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all campaigns visible to the user.
    Meta is the source of truth.
    """
    return await CampaignService.list_campaigns(
        db=db,
        user_id=current_user.id,
    )


# =========================================================
# SYNC CAMPAIGNS FROM META (READ-ONLY)
# =========================================================
@router.post(
    "/sync",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def sync_campaigns_from_meta(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches ALL campaigns from Meta (read-only)
    and stores them idempotently.

    No AI logic.
    No billing logic.
    No enforcement here.
    """
    try:
        return await CampaignService.sync_from_meta(
            db=db,
            user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =========================================================
# AI TOGGLE (ENFORCEMENT COMES IN PHASE 7.3)
# =========================================================
@router.post(
    "/{campaign_id}/ai-toggle",
    response_model=CampaignResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_ai(
    campaign_id: UUID,
    payload: ToggleAIRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enables / disables AI for a campaign.
    Enforcement rules will be applied in Phase 7.3.
    """
    try:
        return await CampaignService.toggle_ai(
            db=db,
            user_id=current_user.id,
            campaign_id=campaign_id,
            enable=payload.enable,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

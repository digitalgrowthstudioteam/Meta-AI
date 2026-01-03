from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest
from app.plans.enforcement import EnforcementError
from app.meta_api.models import MetaOAuthToken


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# DEV MODE USER RESOLUTION (TEMPORARY)
# =========================================================
async def get_dev_user(db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none()


# =========================================================
# LIST CAMPAIGNS (READ-ONLY, CONSISTENT)
# =========================================================
@router.get(
    "/",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)
    if not current_user:
        return []

    # -----------------------------------------
    # META NOT CONNECTED → SIGNAL FRONTEND
    # -----------------------------------------
    result = await db.execute(
        select(MetaOAuthToken)
        .where(
            MetaOAuthToken.user_id == current_user.id,
            MetaOAuthToken.is_active.is_(True),
        )
        .limit(1)
    )
    token = result.scalar_one_or_none()

    if not token:
        # IMPORTANT:
        # - Campaigns page
        # - AI Actions page
        # must detect Meta not connected
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meta account not connected",
        )

    # -----------------------------------------
    # SAFE LIST (EMPTY IS VALID)
    # -----------------------------------------
    try:
        return await CampaignService.list_campaigns(
            db=db,
            user_id=current_user.id,
        )
    except Exception:
        # NEVER crash UI
        return []


# =========================================================
# SYNC CAMPAIGNS FROM META (MANUAL)
# =========================================================
@router.post(
    "/sync",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def sync_campaigns_from_meta(
    db: AsyncSession = Depends(get_db),
):
    current_user = await get_dev_user(db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user available in development mode",
        )

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
# AI TOGGLE (READ-ONLY META SAFE)
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
):
    current_user = await get_dev_user(db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user available in development mode",
        )

    try:
        return await CampaignService.toggle_ai(
            db=db,
            user_id=current_user.id,
            campaign_id=campaign_id,
            enable=payload.enable,
        )

    except EnforcementError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.to_dict(),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

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


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# DEV MODE USER RESOLUTION (TEMPORARY)
# =========================================================
async def get_dev_user(db: AsyncSession) -> Optional[User]:
    """
    Temporary user resolver while auth is disabled.
    Uses first available user in database.

    THIS WILL BE REMOVED when Next.js auth middleware is enabled.
    """
    result = await db.execute(select(User).limit(1))
    return result.scalar_one_or_none()


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
):
    """
    Returns all campaigns visible to the user.
    Meta is the source of truth.
    """

    current_user = await get_dev_user(db)
    if not current_user:
        return []

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
):
    """
    Fetches ALL campaigns from Meta (read-only)
    and stores them idempotently.

    No AI logic.
    No billing logic.
    No enforcement here.
    """

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
# AI TOGGLE (FULL ENFORCEMENT FIREWALL)
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
    """
    Enables / disables AI for a campaign.

    Enforcement failures return:
    - 409 Conflict
    - Structured payload {code, message, action}
    """

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

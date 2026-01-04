from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest
from app.plans.enforcement import EnforcementError
from app.meta_api.models import MetaOAuthToken


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# LIST CAMPAIGNS + CATEGORY VISIBILITY (PHASE 9.2)
# =========================================================
@router.get(
    "",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Phase 9.2:
    - Campaigns + category + confidence + source
    - Read-only
    """

    # -----------------------------
    # DEV MODE (AUTH DISABLED)
    # -----------------------------
    if current_user is None:
        return []

    # -----------------------------
    # PROD MODE
    # -----------------------------
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meta account not connected",
        )

    # Phase 9.2 visibility-aware fetch
    return await CampaignService.list_campaigns_with_visibility(
        db=db,
        user_id=current_user.id,
    )


# =========================================================
# SYNC CAMPAIGNS FROM META
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
    return await CampaignService.sync_from_meta(
        db=db,
        user_id=current_user.id,
    )


# =========================================================
# AI TOGGLE
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

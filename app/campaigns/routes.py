from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount, MetaOAuthToken

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest
from app.plans.enforcement import EnforcementError


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# LIST CAMPAIGNS — With Filters + Cookie Mode
# =========================================================
@router.get(
    "",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def list_campaigns(
    account_id: UUID | None = None,
    status: str | None = None,
    ai_active: str | None = None,
    objective: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    if current_user is None:
        return []

    # Ensure Meta is connected
    token = (
        await db.execute(
            select(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == current_user.id,
                MetaOAuthToken.is_active.is_(True),
            )
            .limit(1)
        )
    ).scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meta account not connected",
        )

    # Base Query
    stmt = (
        select(Campaign)
        .options(selectinload(Campaign.category_map))
        .join(MetaAdAccount, Campaign.ad_account_id == MetaAdAccount.id)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == current_user.id,
            Campaign.is_archived.is_(False),
        )
    )

    # Filter by account_id
    if account_id:
        stmt = stmt.where(Campaign.ad_account_id == account_id)

    # Filter by status
    if status:
        stmt = stmt.where(Campaign.status == status)

    # Filter by objective
    if objective:
        stmt = stmt.where(Campaign.objective == objective)

    # Filter AI (true/false)
    if ai_active is not None and ai_active != "":
        if ai_active.lower() == "true":
            stmt = stmt.where(Campaign.ai_active.is_(True))
        elif ai_active.lower() == "false":
            stmt = stmt.where(Campaign.ai_active.is_(False))

    # Execute query
    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    # Serialize
    return [
        CampaignResponse(
            id=c.id,
            name=c.name,
            objective=c.objective,
            status=c.status,
            ai_active=c.ai_active,
            ai_activated_at=c.ai_activated_at,
            category=c.category_map.final_category if c.category_map else None,
            category_confidence=c.category_map.confidence_score if c.category_map else None,
            category_source=c.category_map.source.value if c.category_map else None,
        )
        for c in campaigns
    ]


# =========================================================
# SYNC CAMPAIGNS — Cookie Based
# =========================================================
@router.post(
    "/sync",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def sync_campaigns_from_meta(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cookie_active_id = request.cookies.get("active_account_id")
    if not cookie_active_id:
        return []

    synced = await CampaignService.sync_from_meta(
        db=db,
        user_id=current_user.id,
        ad_account_ids=[cookie_active_id],
    )

    # Serialize output for response_model compliance
    return [
        CampaignResponse(
            id=c.id,
            name=c.name,
            objective=c.objective,
            status=c.status,
            ai_active=c.ai_active,
            ai_activated_at=c.ai_activated_at,
            category=c.category_map.final_category if c.category_map else None,
            category_confidence=c.category_map.confidence_score if c.category_map else None,
            category_source=c.category_map.source.value if c.category_map else None,
        )
        for c in synced
    ]


# =========================================================
# AI TOGGLE — Plan Enforcement & Structured Errors
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
        campaign = await CampaignService.toggle_ai(
            db=db,
            user_id=current_user.id,
            campaign_id=campaign_id,
            enable=payload.enable,
        )

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            objective=campaign.objective,
            status=campaign.status,
            ai_active=campaign.ai_active,
            ai_activated_at=campaign.ai_activated_at,
            category=campaign.category_map.final_category if campaign.category_map else None,
            category_confidence=campaign.category_map.confidence_score if campaign.category_map else None,
            category_source=campaign.category_map.source.value if campaign.category_map else None,
        )

    except EnforcementError as e:
        # AI LIMIT / PLAN VIOLATION
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.to_dict(),
        )

    except ValueError as e:
        # Campaign not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

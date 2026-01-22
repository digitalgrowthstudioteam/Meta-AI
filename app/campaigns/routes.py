from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount, MetaOAuthToken

from app.core.db_session import get_db
from app.auth.dependencies import (
    get_current_user,
    forbid_impersonated_writes,
)
from app.users.models import User
from app.campaigns.service import CampaignService
from app.campaigns.schemas import CampaignResponse, ToggleAIRequest

# === AI ENFORCEMENT IMPORTS ===
from app.plans.enforcement import PlanEnforcementService, EnforcementError
from app.plans.subscription_models import Subscription

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


# =========================================================
# LIST CAMPAIGNS — SAFE DURING IMPERSONATION (READ-ONLY)
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

    if account_id:
        stmt = stmt.where(Campaign.ad_account_id == account_id)

    if status:
        stmt = stmt.where(Campaign.status == status)

    if objective:
        stmt = stmt.where(Campaign.objective == objective)

    if ai_active is not None and ai_active != "":
        if ai_active.lower() == "true":
            stmt = stmt.where(Campaign.ai_active.is_(True))
        elif ai_active.lower() == "false":
            stmt = stmt.where(Campaign.ai_active.is_(False))

    result = await db.execute(stmt)
    campaigns = result.scalars().all()

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
# SYNC CAMPAIGNS — WRITE → BLOCKED DURING IMPERSONATION
# =========================================================
@router.post(
    "/sync",
    response_model=list[CampaignResponse],
    status_code=status.HTTP_200_OK,
)
async def sync_campaigns_from_meta(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(forbid_impersonated_writes),
):
    cookie_active_id = request.cookies.get("active_account_id")
    if not cookie_active_id:
        return []

    synced = await CampaignService.sync_from_meta(
        db=db,
        user_id=current_user.id,
        ad_account_ids=[cookie_active_id],
    )

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
# PHASE-9 — USAGE SUMMARY (OPTION C2)
# =========================================================
@router.get(
    "/usage",
    status_code=status.HTTP_200_OK,
)
async def campaigns_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    # Fetch active subscription
    sub = await db.scalar(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.id,
            Subscription.status.in_(["trial", "active"]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )

    if not sub:
        return {
            "campaigns_used": 0,
            "campaigns_limit": 0,
            "ai_campaigns_used": 0,
            "ai_campaigns_limit": 0,
        }

    # Count total campaigns (non archived)
    campaigns_used = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.user_id == current_user.id,
            Campaign.is_archived.is_(False),
        )
    ) or 0

    # Count only AI-enabled campaigns (OPTION C2)
    ai_campaigns_used = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.user_id == current_user.id,
            Campaign.ai_active.is_(True),
            Campaign.is_archived.is_(False),
        )
    ) or 0

    return {
        "campaigns_used": campaigns_used,
        "campaigns_limit": sub.campaign_limit_snapshot or 0,
        "ai_campaigns_used": ai_campaigns_used,
        "ai_campaigns_limit": sub.ai_campaign_limit_snapshot or 0,
    }


# =========================================================
# AI TOGGLE — WRITE → BLOCKED DURING IMPERSONATION + ENFORCED
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
    current_user: User = Depends(forbid_impersonated_writes),
):
    # === Load campaign first ===
    campaign = await CampaignService.get_campaign(
        db=db,
        user_id=current_user.id,
        campaign_id=campaign_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    # === ENFORCEMENT ONLY WHEN ENABLING AI ===
    if payload.enable:
        try:
            await PlanEnforcementService.assert_ai_allowed(
                db=db,
                user_id=current_user.id,
                campaign=campaign,
            )
        except EnforcementError as e:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=e.to_dict(),
            )

    try:
        updated = await CampaignService.toggle_ai(
            db=db,
            user_id=current_user.id,
            campaign_id=campaign_id,
            enable=payload.enable,
        )

        return CampaignResponse(
            id=updated.id,
            name=updated.name,
            objective=updated.objective,
            status=updated.status,
            ai_active=updated.ai_active,
            ai_activated_at=updated.ai_activated_at,
            category=updated.category_map.final_category if updated.category_map else None,
            category_confidence=updated.category_map.confidence_score if updated.category_map else None,
            category_source=updated.category_map.source.value if updated.category_map else None,
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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

# -------------------------
# Admin Overrides
# -------------------------
from app.admin.schemas import (
    AdminOverrideCreate,
    AdminOverrideResponse,
)
from app.admin.service import AdminOverrideService

# -------------------------
# Metrics Sync (Phase 6.5)
# -------------------------
from app.admin.metrics_sync_routes import router as metrics_sync_router


router = APIRouter(prefix="/admin", tags=["Admin"])


# =========================
# ADMIN GUARD
# =========================
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# ADMIN OVERRIDES
# =========================
@router.post("/overrides", response_model=AdminOverrideResponse)
async def create_override(
    payload: AdminOverrideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    override = await AdminOverrideService.create_override(
        db=db,
        user_id=payload.user_id,
        extra_ai_campaigns=payload.extra_ai_campaigns,
        force_ai_enabled=payload.force_ai_enabled,
        override_expires_at=payload.override_expires_at,
        reason=payload.reason,
    )

    return override


@router.get("/overrides", response_model=list[AdminOverrideResponse])
async def list_overrides(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminOverrideService.list_overrides(db)


# =========================
# PHASE 10.4 — ADMIN ROLLBACK
# =========================
@router.post("/campaigns/{action_log_id}/rollback")
async def rollback_campaign_action(
    action_log_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    try:
        campaign = await AdminOverrideService.rollback_campaign_action(
            db=db,
            action_log_id=action_log_id,
            admin_user_id=current_user.id,
            reason=reason,
        )
        return {
            "status": "rolled_back",
            "campaign_id": str(campaign.id),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================
# PHASE 11.4 — MANUAL CAMPAIGN PURCHASE / RENEWAL
# =========================
@router.post("/campaigns/{campaign_id}/manual-grant")
async def grant_or_renew_manual_campaign(
    campaign_id: UUID,
    valid_from: date,
    valid_till: date,
    price_paid: float,
    plan_label: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    try:
        campaign = await AdminOverrideService.grant_or_renew_manual_campaign(
            db=db,
            campaign_id=campaign_id,
            admin_user_id=current_user.id,
            valid_from=valid_from,
            valid_till=valid_till,
            price_paid=price_paid,
            plan_label=plan_label,
            reason=reason,
        )
        return {
            "status": "manual_campaign_active",
            "campaign_id": str(campaign.id),
            "valid_till": str(campaign.manual_valid_till),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =========================
# METRICS SYNC ROUTES
# =========================
router.include_router(metrics_sync_router)

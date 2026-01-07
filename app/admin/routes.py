from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

# -------------------------
# Admin Schemas / Services
# -------------------------
from app.admin.schemas import (
    AdminOverrideCreate,
    AdminOverrideResponse,
)
from app.admin.service import AdminOverrideService

# -------------------------
# Plan / Subscription Enforcement
# -------------------------
from app.plans.enforcement import PlanEnforcementService

# -------------------------
# Audit Models
# -------------------------
from app.campaigns.models import CampaignActionLog

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
# ADMIN DASHBOARD
# =========================
@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminOverrideService.get_dashboard_stats(db=db)


# =========================
# ADMIN USERS (REQUIRED)
# =========================
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


# =========================
# GLOBAL SETTINGS
# =========================
@router.get("/settings")
async def get_global_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    settings = await AdminOverrideService.get_global_settings(db=db)

    return {
        "site_name": settings.site_name,
        "dashboard_title": settings.dashboard_title,
        "logo_url": settings.logo_url,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "meta_sync_enabled": settings.meta_sync_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "updated_at": settings.updated_at.isoformat(),
    }


@router.put("/settings")
async def update_global_settings(
    payload: dict,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    settings = await AdminOverrideService.update_global_settings(
        db=db,
        admin_user_id=current_user.id,
        updates=payload,
        reason=reason,
    )

    return {
        "status": "updated",
        "settings": {
            "site_name": settings.site_name,
            "dashboard_title": settings.dashboard_title,
            "logo_url": settings.logo_url,
            "ai_globally_enabled": settings.ai_globally_enabled,
            "meta_sync_enabled": settings.meta_sync_enabled,
            "maintenance_mode": settings.maintenance_mode,
            "updated_at": settings.updated_at.isoformat(),
        },
    }


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
    return await AdminOverrideService.create_override(
        db=db,
        user_id=payload.user_id,
        extra_ai_campaigns=payload.extra_ai_campaigns,
        force_ai_enabled=payload.force_ai_enabled,
        override_expires_at=payload.override_expires_at,
        reason=payload.reason,
    )


@router.get("/overrides", response_model=list[AdminOverrideResponse])
async def list_overrides(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminOverrideService.list_overrides(db)


# =========================
# ADMIN ROLLBACK
# =========================
@router.post("/campaigns/{action_log_id}/rollback")
async def rollback_campaign_action(
    action_log_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

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


# =========================
# SUBSCRIPTION EXPIRY CRON
# =========================
@router.post("/cron/subscription-expiry")
async def run_subscription_expiry_cron(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    affected = await PlanEnforcementService.enforce_subscription_expiry(db=db)
    return {
        "status": "ok",
        "expired_campaigns_disabled": affected,
    }


# =========================
# AUDIT APIs (READ-ONLY)
# =========================
@router.get("/audit/actions")
async def list_campaign_action_logs(
    *,
    campaign_id: UUID | None = Query(default=None),
    actor_type: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    stmt = select(CampaignActionLog).order_by(
        CampaignActionLog.created_at.desc()
    )

    if campaign_id:
        stmt = stmt.where(CampaignActionLog.campaign_id == campaign_id)
    if actor_type:
        stmt = stmt.where(CampaignActionLog.actor_type == actor_type)

    result = await db.execute(stmt.limit(limit))
    logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "campaign_id": str(log.campaign_id),
            "actor_type": log.actor_type,
            "action_type": log.action_type,
            "reason": log.reason,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/audit/actions/{action_log_id}")
async def get_campaign_action_log(
    action_log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(CampaignActionLog).where(
            CampaignActionLog.id == action_log_id
        )
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {
        "id": str(log.id),
        "campaign_id": str(log.campaign_id),
        "actor_type": log.actor_type,
        "action_type": log.action_type,
        "reason": log.reason,
        "before_state": log.before_state,
        "after_state": log.after_state,
        "created_at": log.created_at.isoformat(),
    }


# =========================
# METRICS SYNC ROUTES
# =========================
router.include_router(metrics_sync_router)

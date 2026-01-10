from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.plans.subscription_models import Subscription, SubscriptionAddon

from app.admin.models import AdminAuditLog
from app.admin.service import AdminOverrideService
from app.admin.pricing_service import AdminPricingConfigService

from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)

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
# ADMIN USERS (READ ONLY)
# =========================
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    response = []

    for u in users:
        sub_status = await db.scalar(
            select(Subscription.status)
            .where(Subscription.user_id == u.id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )

        ai_campaigns = await db.scalar(
            select(func.count(Campaign.id))
            .where(
                Campaign.user_id == u.id,
                Campaign.ai_active.is_(True),
            )
        )

        response.append(
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login_at": (
                    u.last_login_at.isoformat()
                    if getattr(u, "last_login_at", None)
                    else None
                ),
                "subscription_status": sub_status,
                "ai_campaigns_active": ai_campaigns or 0,
            }
        )

    return response

# ==========================================================
# PHASE 7.2 — META API SETTINGS (AUDITED)
# ==========================================================
@router.get("/meta-settings")
async def get_meta_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    settings = await AdminOverrideService.get_global_settings(db)
    return {
        "meta_sync_enabled": settings.meta_sync_enabled,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "site_name": settings.site_name,
        "dashboard_title": settings.dashboard_title,
        "logo_url": settings.logo_url,
    }

@router.post("/meta-settings")
async def update_meta_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    allowed_fields = [
        "meta_sync_enabled",
        "ai_globally_enabled",
        "maintenance_mode",
        "site_name",
        "dashboard_title",
        "logo_url",
    ]

    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    reason = payload.get("reason")
    if not updates or not reason:
        raise HTTPException(400, "Updates and reason are required")

    updated_settings = await AdminOverrideService.update_global_settings(
        db=db,
        admin_user_id=current_user.id,
        updates=updates,
        reason=reason,
    )

    return {
        "status": "updated",
        "meta_sync_enabled": updated_settings.meta_sync_enabled,
        "ai_globally_enabled": updated_settings.ai_globally_enabled,
        "maintenance_mode": updated_settings.maintenance_mode,
        "site_name": updated_settings.site_name,
        "dashboard_title": updated_settings.dashboard_title,
        "logo_url": updated_settings.logo_url,
    }

# ==========================================================
# PHASE 7.13 — ADMIN SLOT CONTROLS (AUDITED)
# ==========================================================
@router.post("/slots/{addon_id}/extend")
async def admin_extend_slot_expiry(
    addon_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    days = payload.get("days")
    reason = payload.get("reason")
    if not days or not reason:
        raise HTTPException(400, "days and reason required")

    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")

    before_state = {"expires_at": addon.expires_at.isoformat()}
    addon.expires_at = addon.expires_at + timedelta(days=int(days))
    after_state = {"expires_at": addon.expires_at.isoformat()}

    db.add(
        AdminAuditLog(
            admin_user_id=current_user.id,
            target_type="slot_addon",
            target_id=addon.id,
            action="extend_slot_expiry",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()
    return {"status": "extended", "expires_at": addon.expires_at.isoformat()}


@router.post("/slots/{addon_id}/expire")
async def admin_force_expire_slot(
    addon_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "reason required")
    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")

    before_state = {"expires_at": addon.expires_at.isoformat()}
    addon.expires_at = datetime.utcnow()
    after_state = {"expires_at": addon.expires_at.isoformat()}

    db.add(
        AdminAuditLog(
            admin_user_id=current_user.id,
            target_type="slot_addon",
            target_id=addon.id,
            action="force_expire_slot",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()
    return {"status": "expired"}


@router.post("/slots/{addon_id}/adjust")
async def admin_adjust_slot_quantity(
    addon_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    new_quantity = payload.get("extra_ai_campaigns")
    reason = payload.get("reason")
    if new_quantity is None or not reason:
        raise HTTPException(400, "extra_ai_campaigns and reason required")

    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")

    before_state = {"extra_ai_campaigns": addon.extra_ai_campaigns}
    addon.extra_ai_campaigns = int(new_quantity)
    after_state = {"extra_ai_campaigns": addon.extra_ai_campaigns}

    db.add(
        AdminAuditLog(
            admin_user_id=current_user.id,
            target_type="slot_addon",
            target_id=addon.id,
            action="adjust_slot_quantity",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()
    return {"status": "adjusted", "extra_ai_campaigns": addon.extra_ai_campaigns}

# ==========================================================
# PHASE 7 — PRICING CONFIG (ADMIN ONLY)
# ==========================================================
@router.get("/pricing-config/active")
async def get_active_pricing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminPricingConfigService.get_active_config(db)


@router.get("/pricing-config")
async def list_pricing_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminPricingConfigService.list_configs(db)


@router.post("/pricing-config")
async def create_pricing_config(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    required = [
        "plan_pricing",
        "slot_packs",
        "currency",
        "tax_percentage",
        "invoice_prefix",
        "razorpay_mode",
        "reason",
    ]
    for field in required:
        if field not in payload:
            raise HTTPException(400, f"{field} is required")

    return await AdminPricingConfigService.create_config(
        db=db,
        admin_user_id=current_user.id,
        plan_pricing=payload["plan_pricing"],
        slot_packs=payload["slot_packs"],
        currency=payload["currency"],
        tax_percentage=payload["tax_percentage"],
        invoice_prefix=payload["invoice_prefix"],
        invoice_notes=payload.get("invoice_notes"),
        razorpay_mode=payload["razorpay_mode"],
        reason=payload["reason"],
    )


@router.post("/pricing-config/{config_id}/activate")
async def activate_pricing_config(
    config_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "reason required")

    await AdminPricingConfigService.activate_config(
        db=db,
        admin_user_id=current_user.id,
        config_id=config_id,
        reason=reason,
    )

    return {"status": "activated"}

# ==========================================================
# PHASE 6 — ADMIN AUDIT LOG VIEWER
# ==========================================================
@router.get("/audit-logs")
async def list_admin_audit_logs(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
    target_type: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    require_admin(current_user)
    stmt = select(AdminAuditLog)
    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)

    result = await db.execute(
        stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "admin_user_id": str(l.admin_user_id),
            "target_type": l.target_type,
            "target_id": str(l.target_id) if l.target_id else None,
            "action": l.action,
            "reason": l.reason,
            "rollback_token": (
                str(l.rollback_token) if l.rollback_token else None
            ),
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]

# ==========================================================
# PHASE 6.5 — ROLLBACK EXECUTION
# ==========================================================
@router.post("/rollback")
async def rollback_by_token(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)
    rollback_token = payload.get("rollback_token")
    reason = payload.get("reason")
    if not rollback_token or not reason:
        raise HTTPException(400, "rollback_token and reason required")

    await AdminOverrideService.rollback_by_token(
        db=db,
        admin_user_id=current_user.id,
        rollback_token=UUID(rollback_token),
        reason=reason,
    )
    return {"status": "rolled_back"}

# ==========================================================
# PHASE 3.2 — SUPPORT TOOLS
# ==========================================================
async def _log_support_action(
    *,
    db: AsyncSession,
    admin_user: User,
    target_user_id: UUID,
    action: str,
    reason: str,
):
    db.add(
        AdminAuditLog(
            admin_user_id=admin_user.id,
            target_type="user",
            target_id=target_user_id,
            action=action,
            before_state={},
            after_state={},
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )
    await db.commit()


@router.post("/support/force_meta_resync")
async def force_meta_resync(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await CampaignDailyMetricsSyncService.force_user_resync(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="force_meta_resync",
        reason=reason,
    )

    return {"status": "ok"}

# =========================
# METRICS SYNC ROUTES
# =========================
router.include_router(metrics_sync_router)

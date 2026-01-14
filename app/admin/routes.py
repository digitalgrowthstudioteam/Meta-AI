from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from uuid import UUID
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign
from app.plans.subscription_models import Subscription, SubscriptionAddon
from app.billing.invoice_models import Invoice
from app.billing.payment_models import Payment  # <--- ADDED for Razorpay Logs
from app.admin.models import AdminAuditLog
from app.admin.service import AdminOverrideService
from app.admin.pricing_service import AdminPricingConfigService
from app.admin.rbac import assert_admin_permission
from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)
from app.admin.metrics_sync_routes import router as metrics_sync_router

# Try importing AIAction safely
try:
    from app.ai_engine.models.action_models import AIAction
except ImportError:
    AIAction = None

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
    assert_admin_permission(current_user, "system:read")
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
    assert_admin_permission(current_user, "users:read")
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

# =========================
# ADMIN INVOICES (READ ONLY)
# =========================
@router.get("/invoices")
async def list_admin_invoices(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "billing:read")
    
    stmt = select(Invoice).order_by(Invoice.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    
    return [
        {
            "id": str(inv.id),
            "user_id": str(inv.user_id),
            "amount": inv.amount,
            "currency": inv.currency,
            "status": inv.status,
            "invoice_number": inv.invoice_number,
            "pdf_url": inv.pdf_url,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invoices
    ]

# =========================
# ADMIN RAZORPAY LOGS (ADDED)
# =========================
@router.get("/razorpay-logs")
async def list_razorpay_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    # Fetch recent payments
    stmt = select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    payments = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "razorpay_order_id": p.razorpay_order_id,
            "razorpay_payment_id": p.razorpay_payment_id,
            "amount": p.amount,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]

# =========================
# ADMIN AI ACTIONS (ADDED)
# =========================
@router.get("/ai-actions")
async def list_ai_actions(
    limit: int = 50,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    if AIAction is None:
        return []

    stmt = select(AIAction).order_by(AIAction.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(AIAction.status == status)
        
    result = await db.execute(stmt)
    actions = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "campaign_id": str(a.campaign_id),
            "action_type": a.action_type,
            "status": a.status,
            "reason": a.reason,
            "created_at": a.created_at.isoformat()
        }
        for a in actions
    ]

@router.get("/ai-suggestions")
async def list_ai_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    # Reuse logic for pending actions
    return await list_ai_actions(limit=20, status="pending", db=db, current_user=current_user)

# =========================
# ADMIN REPORTS (ADDED)
# =========================
@router.get("/reports")
async def list_admin_reports(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return []  # Return empty list until Report model is active

# =========================
# METRIC SYNC STATUS (ADDED)
# =========================
@router.get("/metrics/sync-status")
async def get_metrics_sync_status(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return {
        "status": "healthy",
        "last_sync": datetime.utcnow().isoformat(),
        "pending_accounts": 0
    }

# =========================
# RISK ALERTS (ADDED)
# =========================
@router.get("/risk/alerts")
async def get_risk_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    stmt = select(User).where(User.is_active == False).limit(20)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "user_id": str(u.id),
            "email": u.email,
            "reason": "Account Inactive/Frozen",
            "detected_at": datetime.utcnow().isoformat()
        }
        for u in users
    ]

# ==========================================================
# PHASE 7.2 — META API SETTINGS
# ==========================================================
@router.get("/meta-settings")
async def get_meta_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "system:read")
    settings = await AdminOverrideService.get_global_settings(db)
    return {
        "meta_sync_enabled": settings.meta_sync_enabled,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "site_name": settings.site_name,
        "dashboard_title": settings.dashboard_title,
        "logo_url": settings.logo_url,
        "expansion_mode_enabled": settings.expansion_mode_enabled,
        "fatigue_mode_enabled": settings.fatigue_mode_enabled,
        "auto_pause_enabled": settings.auto_pause_enabled,
        "confidence_gating_enabled": settings.confidence_gating_enabled,
        "max_optimizations_per_day": settings.max_optimizations_per_day,
        "max_expansions_per_day": settings.max_expansions_per_day,
        "ai_refresh_frequency_minutes": settings.ai_refresh_frequency_minutes,
    }

@router.post("/meta-settings")
async def update_meta_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "system:write")
    forbid_impersonated_writes(current_user)

    allowed_fields = [
        "meta_sync_enabled",
        "ai_globally_enabled",
        "maintenance_mode",
        "site_name",
        "dashboard_title",
        "logo_url",
        "expansion_mode_enabled",
        "fatigue_mode_enabled",
        "auto_pause_enabled",
        "confidence_gating_enabled",
        "max_optimizations_per_day",
        "max_expansions_per_day",
        "ai_refresh_frequency_minutes",
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
    }

# ==========================================================
# PHASE 7.13 — ADMIN SLOT CONTROLS
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
# PHASE 7 — PRICING CONFIG
# ==========================================================
@router.get("/pricing-config/active")
async def get_active_pricing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "billing:read")
    return await AdminPricingConfigService.get_active_config(db)


@router.get("/pricing-config")
async def list_pricing_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "billing:read")
    return await AdminPricingConfigService.list_configs(db)


@router.post("/pricing-config")
async def create_pricing_config(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "billing:write")
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
    assert_admin_permission(current_user, "billing:write")
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
# 🔥 Matched to Frontend: /audit/actions
@router.get("/audit/actions")
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
    assert_admin_permission(current_user, "system:write")
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
    assert_admin_permission(current_user, "support:execute")
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

# ==========================================================
# RISK ACTIONS
# ==========================================================
@router.post("/risk/freeze-user")
async def risk_freeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "users:write")
    forbid_impersonated_writes(current_user)

    user_id = payload.get("user_id")
    reason = payload.get("reason")

    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.freeze_user(
        db=db,
        admin_user_id=current_user.id,
        target_user_id=UUID(user_id),
        reason=reason,
    )

    return {"status": "user_frozen"}


@router.post("/risk/unfreeze-user")
async def risk_unfreeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "users:write")
    forbid_impersonated_writes(current_user)

    user_id = payload.get("user_id")
    reason = payload.get("reason")

    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.unfreeze_user(
        db=db,
        admin_user_id=current_user.id,
        target_user_id=UUID(user_id),
        reason=reason,
    )

    return {"status": "user_unfrozen"}


@router.post("/risk/disable-user-ai")
async def risk_disable_user_ai(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(current_user, "users:write")
    forbid_impersonated_writes(current_user)

    user_id = payload.get("user_id")
    reason = payload.get("reason")

    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.disable_user_ai(
        db=db,
        admin_user_id=current_user.id,
        target_user_id=UUID(user_id),
        reason=reason,
    )

    return {"status": "ai_disabled_for_user"}

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.plans.subscription_models import Subscription, SubscriptionAddon
from app.plans.models import Plan
from app.billing.invoice_models import Invoice
from app.billing.payment_models import Payment
from app.admin.models import AdminAuditLog
from app.admin.service import AdminOverrideService
from app.admin.pricing_service import AdminPricingConfigService
from app.admin.rbac import assert_admin_permission
from app.meta_insights.services.campaign_daily_metrics_sync_service import CampaignDailyMetricsSyncService
from app.admin.metrics_sync_routes import router as metrics_sync_router
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount

try:
    from app.ai_engine.models.action_models import AIAction
except ImportError:
    AIAction = None

router = APIRouter(prefix="/admin", tags=["Admin"])

ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}

def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# DASHBOARD
# =========================
@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:read")
    return await AdminOverrideService.get_dashboard_stats(db=db)


# =========================
# USERS LIST
# =========================
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:read")
    
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
        
        response.append(
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login_at": (
                    u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None
                ),
                "subscription_status": sub_status,
                "ai_campaigns_active": 0,
            }
        )

    return response


# =========================
# USER DETAIL BASE
# =========================
@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user)
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:read")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    meta_stmt = (
        select(MetaAdAccount)
        .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
        .where(UserMetaAdAccount.user_id == user_id)
        .order_by(MetaAdAccount.connected_at.desc())
    )
    meta_res = await db.execute(meta_stmt)
    meta_accounts = [
        {
            "id": str(m.id),
            "name": m.account_name,
            "status": "active" if m.is_active else "inactive",
            "last_sync_at": None,
        }
        for m in meta_res.scalars().all()
    ]

    camp_stmt = select(Campaign).order_by(Campaign.created_at.desc())
    camp_res = await db.execute(camp_stmt)
    campaigns = []
    for c in camp_res.scalars().all():
        campaigns.append(
            {
                "id": str(c.id),
                "name": c.name,
                "objective": c.objective,
                "ai_active": c.ai_active,
                "status": c.status,
                "last_ai_action_at": None,
            }
        )

    inv_stmt = (
        select(Invoice)
        .where(Invoice.user_id == user_id)
        .order_by(Invoice.created_at.desc())
        .limit(50)
    )
    inv_res = await db.execute(inv_stmt)
    invoices = [
        {
            "id": str(i.id),
            "amount": i.total_amount,
            "status": i.status,
            "created_at": i.created_at.isoformat(),
        }
        for i in inv_res.scalars().all()
    ]

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login_at": (
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
        },
        "meta_accounts": meta_accounts,
        "campaigns": campaigns,
        "invoices": invoices,
        "ai_actions": [],
    }


# ===============================
# USER SUBSCRIPTION DETAIL
# ===============================
@router.get("/users/{user_id}/subscription")
async def get_user_subscription_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    current = await db.execute(
        select(Subscription, Plan.name)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.user_id == user_id)
        .where(Subscription.status.in_(["active", "trial"]))
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    current_row = current.first()

    history_res = await db.execute(
        select(Subscription, Plan.name)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.user_id == user_id)
        .order_by(desc(Subscription.created_at))
        .limit(20)
    )
    history = history_res.all()

    addons_res = await db.execute(
        select(SubscriptionAddon)
        .join(Subscription, Subscription.id == SubscriptionAddon.subscription_id)
        .where(Subscription.user_id == user_id)
    )
    addons = addons_res.scalars().all()

    return {
        "current": (
            {
                "id": str(current_row[0].id),
                "plan_id": current_row[0].plan_id,
                "plan_name": current_row[1],
                "status": current_row[0].status,
                "starts_at": current_row[0].starts_at.isoformat(),
                "ends_at": current_row[0].ends_at.isoformat() if current_row[0].ends_at else None,
                "pricing_mode": current_row[0].pricing_mode,
                "custom_price": current_row[0].custom_price,
                "custom_duration_months": current_row[0].custom_duration_months,
                "custom_duration_days": current_row[0].custom_duration_days,
                "never_expires": current_row[0].never_expires,
                "admin_notes": current_row[0].admin_notes,
            }
            if current_row else None
        ),
        "history": [
            {
                "id": str(s.id),
                "plan_id": s.plan_id,
                "plan_name": plan_name,
                "status": s.status,
                "starts_at": s.starts_at.isoformat(),
                "ends_at": s.ends_at.isoformat() if s.ends_at else None,
                "pricing_mode": s.pricing_mode,
                "custom_price": s.custom_price,
                "never_expires": s.never_expires,
            }
            for (s, plan_name) in history
        ],
        "addons": [
            {
                "id": str(a.id),
                "subscription_id": str(a.subscription_id),
                "extra_ai_campaigns": a.extra_ai_campaigns,
                "expires_at": a.expires_at.isoformat() if a.expires_at else None,
            }
            for a in addons
        ],
    }


# =========================
# INVOICES
# =========================
@router.get("/invoices")
async def list_admin_invoices(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")
    
    stmt = select(Invoice).order_by(Invoice.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    
    return [
        {
            "id": str(inv.id),
            "user_id": str(inv.user_id),
            "amount": inv.total_amount,
            "currency": inv.currency,
            "status": inv.status,
            "invoice_number": inv.invoice_number,
            "pdf_url": inv.pdf_url,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invoices
    ]


# =========================
# RAZORPAY LOGS
# =========================
@router.get("/razorpay")
async def list_razorpay_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
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
# AI ACTIONS
# =========================
@router.get("/ai-actions")
async def list_ai_actions(
    limit: int = 50,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    stmt = select(CampaignActionLog).order_by(CampaignActionLog.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(CampaignActionLog.actor_type.ilike(status))

    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "campaign_id": str(l.campaign_id),
            "action_type": l.action_type,
            "status": l.actor_type.upper() if l.actor_type else None,
            "reason": l.reason,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/ai-suggestions")
async def list_ai_suggestions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    return await list_ai_actions(limit=20, status="pending", db=db, current_user=current_user)


# =========================
# REPORTS
# =========================
@router.get("/reports")
async def list_admin_reports(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return []


# =========================
# METRIC SYNC
# =========================
@router.get("/metrics/sync-status")
async def get_metrics_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return {
        "status": "healthy",
        "last_sync": datetime.utcnow().isoformat(),
        "pending_accounts": 0
    }


# =========================
# RISK
# =========================
@router.get("/risk")
async def get_risk_dashboard(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return {
        "high_risk_users": 0,
        "flagged_campaigns": 0,
        "status": "secure"
    }


@router.get("/risk/timeline")
async def get_risk_timeline(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return []


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


# =========================
# META SETTINGS
# =========================
@router.get("/meta-settings")
async def get_meta_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:read")
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
        "max_expansions_per_day": settings.max_expansions_partner_day,
        "ai_refresh_frequency_minutes": settings.ai_refresh_frequency_minutes,
    }


@router.post("/meta-settings")
async def update_meta_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:write")
    forbid_impersonated_writes(current_user)

    allowed_fields = [
        "meta_sync_enabled", "ai_globally_enabled", "maintenance_mode",
        "site_name", "dashboard_title", "logo_url", "expansion_mode_enabled",
        "fatigue_mode_enabled", "auto_pause_enabled", "confidence_gating_enabled",
        "max_optimizations_per_day", "max_expansions_per_day", "ai_refresh_frequency_minutes",
    ]

    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    reason = payload.get("reason")
    if not updates or not reason:
        raise HTTPException(400, "Updates and reason are required")

    await AdminOverrideService.update_global_settings(
        db=db,
        admin_user_id=current_user.id,
        updates=updates,
        reason=reason,
    )

    return {"status": "updated"}


# =========================
# AUDIT LOGS
# =========================
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

    result = await db.execute(stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "admin_user_id": str(l.admin_user_id),
            "target_type": l.target_type,
            "target_id": str(l.target_id) if l.target_id else None,
            "action": l.action,
            "reason": l.reason,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


# =========================
# RISK ACTIONS
# =========================
@router.post("/risk/freeze-user")
async def risk_freeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")
    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.freeze_user(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )
    return {"status": "user_frozen"}


@router.post("/risk/unfreeze-user")
async def risk_unfreeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")
    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.unfreeze_user(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )
    return {"status": "user_unfrozen"}


@router.post("/risk/disable-user-ai")
async def risk_disable_user_ai(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")
    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(400, "user_id and reason required")

    await AdminOverrideService.disable_user_ai(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )
    return {"status": "ai_disabled_for_user"}


# =========================
# PRICING CONFIG
# =========================
@router.get("/pricing-config/active")
async def get_active_pricing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminPricingConfigService.get_active_config(db)


@router.get("/pricing-config")
async def list_pric
awaiter(db)  # truncated for brevity


# =========================
# SLOT CONTROLS
# =========================
@router.post("/slots/{addon_id}/extend")
async def admin_extend_slot_expiry(
    addon_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    days = payload.get("days")
    reason = payload.get("reason")
    if not days or not reason:
        raise HTTPException(400, "days and reason required")
    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")
    addon.expires_at = addon.expires_at + timedelta(days=int(days))
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
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "reason required")
    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")
    addon.expires_at = datetime.utcnow()
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
    new_quantity = payload.get("extra_ai_campaigns")
    reason = payload.get("reason")
    if new_quantity is None or not reason:
        raise HTTPException(400, "extra_ai_campaigns and reason required")
    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(404, "Slot addon not found")
    addon.extra_ai_campaigns = int(new_quantity)
    await db.commit()
    return {"status": "adjusted", "extra_ai_campaigns": addon.extra_ai_campaigns}


# =========================
# ASSIGN SUBSCRIPTION
# =========================
@router.post("/subscriptions/assign")
async def admin_assign_subscription(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:write")

    user_id = payload.get("user_id")
    plan_id = payload.get("plan_id")
    pricing_mode = payload.get("pricing_mode")
    custom_price = payload.get("custom_price")
    custom_months = payload.get("custom_duration_months")
    custom_days = payload.get("custom_duration_days")
    never_expires = payload.get("never_expires", False)
    admin_notes = payload.get("admin_notes")

    if not user_id or not plan_id or not pricing_mode:
        raise HTTPException(400, "user_id, plan_id, pricing_mode required")

    await db.execute(
        update(Subscription)
        .where(Subscription.user_id == UUID(user_id))
        .where(Subscription.status.in_(["active", "trial"]))
        .values(status="expired", is_active=False)
    )

    starts_at = datetime.utcnow()
    ends_at = None

    if not never_expires:
        if custom_months:
            ends_at = starts_at + timedelta(days=30 * int(custom_months))
        if custom_days:
            extra = timedelta(days=int(custom_days))
            ends_at = (ends_at + extra) if ends_at else (starts_at + extra)

    sub = Subscription(
        id=uuid4(),
        user_id=UUID(user_id),
        plan_id=int(plan_id),
        status="active",
        starts_at=starts_at,
        ends_at=ends_at,
        is_trial=False,
        grace_ends_at=None,
        ai_campaign_limit_snapshot=0,
        is_active=True,
        created_by_admin=True,
        assigned_by_admin=True,
        created_at=datetime.utcnow(),
        billing_cycle="manual",
        pricing_mode=pricing_mode,
        custom_price=custom_price,
        custom_duration_months=custom_months,
        custom_duration_days=custom_days,
        never_expires=never_expires,
        admin_notes=admin_notes,
    )

    db.add(sub)

    audit = AdminAuditLog(
        admin_user_id=current_user.id,
        target_type="subscription",
        target_id=sub.id,
        action="admin_assign_subscription",
        before_state={},
        after_state={
            "user_id": user_id,
            "plan_id": plan_id,
            "pricing_mode": pricing_mode,
            "custom_price": custom_price,
            "custom_duration_months": custom_months,
            "custom_duration_days": custom_days,
            "never_expires": never_expires,
        },
        reason=payload.get("reason", "manual assignment"),
        rollback_token=uuid4(),
        created_at=datetime.utcnow(),
    )

    db.add(audit)
    await db.commit()

    return {"status": "assigned", "subscription_id": str(sub.id)}


# =========================
# INCLUDE METRICS ROUTES
# =========================
router.include_router(metrics_sync_router)

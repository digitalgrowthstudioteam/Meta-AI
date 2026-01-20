from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import razorpay

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.plans.subscription_models import Subscription, SubscriptionAddon
from app.plans.models import Plan
from app.billing.invoice_models import Invoice
from app.billing.payment_models import Payment
from app.admin.rbac import assert_admin_permission
from app.admin.models import AdminAuditLog
from app.billing.provider_models import BillingProvider
from app.core.crypto import CryptoService
from app.core.config import settings

router = APIRouter(prefix="/billing", tags=["Admin Billing"])

ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}

def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 6:
        return key[:2] + "***"
    return key[:-6] + "***"

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
        raise HTTPException(status_code=404, detail="User not found")

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
        raise HTTPException(status_code=400, detail="days and reason required")

    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(status_code=404, detail="Slot addon not found")

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
        raise HTTPException(status_code=400, detail="reason required")

    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(status_code=404, detail="Slot addon not found")

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
        raise HTTPException(status_code=400, detail="extra_ai_campaigns and reason required")

    addon = await db.get(SubscriptionAddon, addon_id)
    if not addon:
        raise HTTPException(status_code=404, detail="Slot addon not found")

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
    forbid_impersonated_writes(current_user)

    user_id = payload.get("user_id")
    plan_id = payload.get("plan_id")
    pricing_mode = payload.get("pricing_mode")
    custom_price = payload.get("custom_price")
    custom_months = payload.get("custom_duration_months")
    custom_days = payload.get("custom_duration_days")
    never_expires = payload.get("never_expires", False)
    admin_notes = payload.get("admin_notes")

    if not user_id or not plan_id or not pricing_mode:
        raise HTTPException(status_code=400, detail="user_id, plan_id, pricing_mode required")

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

# ===============================
# BILLING PROVIDER CONFIG
# ===============================

@router.get("/providers/ping")
async def providers_ping():
    return {"status": "ok"}

@router.get("/providers/config")
async def get_billing_providers_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    q = select(BillingProvider).order_by(BillingProvider.created_at.desc())
    result = await db.execute(q)
    rows = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "provider": r.provider,
            "mode": r.mode,
            "key_id": mask_key(r.key_id),
            "has_secret": bool(r.key_secret_encrypted),
            "active": r.active,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]

@router.post("/providers/config")
async def upsert_billing_provider_config(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:write")

    provider = payload.get("provider", "razorpay")
    mode = payload.get("mode")
    key_id = payload.get("key_id")
    key_secret = payload.get("key_secret")
    webhook_secret = payload.get("webhook_secret")

    if mode not in ("TEST", "LIVE"):
        raise HTTPException(400, detail="mode must be TEST or LIVE")

    if not key_id or not key_secret:
        raise HTTPException(400, detail="key_id and key_secret required")

    # deactivate previous rows for EXACT-ONE rule
    await db.execute(
        update(BillingProvider)
        .where(BillingProvider.provider == provider)
        .where(BillingProvider.mode == mode)
        .values(active=False)
    )

    existing = await db.scalar(
        select(BillingProvider)
        .where(BillingProvider.provider == provider)
        .where(BillingProvider.mode == mode)
        .limit(1)
    )

    encrypted_secret = CryptoService.encrypt_secret(key_secret)
    encrypted_webhook = (
        CryptoService.encrypt_secret(webhook_secret)
        if webhook_secret else None
    )

    if existing:
        existing.key_id = key_id
        existing.key_secret_encrypted = encrypted_secret
        existing.webhook_secret_encrypted = encrypted_webhook
        existing.active = True
        existing.updated_at = datetime.utcnow()
    else:
        row = BillingProvider(
            provider=provider,
            mode=mode,
            key_id=key_id,
            key_secret_encrypted=encrypted_secret,
            webhook_secret_encrypted=encrypted_webhook,
            active=True,
        )
        db.add(row)

    await db.commit()
    return {"status": "ok"}

# ===============================
# NEW: GET ACTIVE CONFIG (ENV + DB)
# ===============================
@router.get("/config")
async def get_active_billing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    mode = settings.RAZORPAY_MODE

    row = await db.scalar(
        select(BillingProvider)
        .where(BillingProvider.provider == "razorpay")
        .where(BillingProvider.mode == mode)
        .where(BillingProvider.active.is_(True))
        .limit(1)
    )

    if row:
        return {
            "provider": "razorpay",
            "mode": mode,
            "key_id": mask_key(row.key_id),
            "has_secret": True,
            "source": "db",
        }

    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET

    if key_id and key_secret:
        return {
            "provider": "razorpay",
            "mode": mode,
            "key_id": mask_key(key_id),
            "has_secret": True,
            "source": "env",
        }

    raise HTTPException(404, detail="No active Razorpay config found")

# ===============================
# NEW: TEST CONNECTION (SELECTED_MODE)
# ===============================
@router.post("/config/test")
async def test_billing_connection(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    mode = payload.get("mode")
    if mode not in ("TEST", "LIVE"):
        raise HTTPException(400, detail="mode must be TEST or LIVE")

    row = await db.scalar(
        select(BillingProvider)
        .where(BillingProvider.provider == "razorpay")
        .where(BillingProvider.mode == mode)
        .where(BillingProvider.active.is_(True))
        .limit(1)
    )

    if row:
        key_id = row.key_id
        key_secret = CryptoService.decrypt_secret(row.key_secret_encrypted)
    else:
        key_id = settings.RAZORPAY_KEY_ID
        key_secret = settings.RAZORPAY_KEY_SECRET

    if not key_id or not key_secret:
        raise HTTPException(400, detail="No credentials available for test")

    client = razorpay.Client(auth=(key_id, key_secret))

    try:
        client.payment.all(count=1)
    except Exception as e:
        raise HTTPException(400, detail=f"Razorpay test failed: {str(e)}")

    return {"status": "ok"}

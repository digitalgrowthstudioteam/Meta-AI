import json
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db_session import get_db
from app.core.config import settings
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.plans.subscription_models import Subscription
from app.plans.models import Plan

router = APIRouter(prefix="/billing/webhook", tags=["Billing Webhooks"])

IST = ZoneInfo("Asia/Kolkata")


def ist_now_utc():
    """Generate IST timestamp converted to UTC for DB."""
    return datetime.now(IST).astimezone(timezone.utc)


def generate_invoice_no():
    return f"INV-{datetime.now(IST).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body.decode())
    event = payload.get("event")

    # SAFETY: We must handle multiple event types
    if event == "subscription.activated":
        return await handle_subscription_activated(payload, db)

    if event == "subscription.charged":
        return await handle_subscription_charged(payload, db)

    if event == "invoice.paid":
        return await handle_invoice_paid(payload, db)

    if event == "payment.captured":
        return await handle_payment_captured(payload, db)

    if event == "payment.failed":
        return await handle_payment_failed(payload, db)

    return {"status": "ignored", "reason": "unsupported_event"}


# ======================================================
# 1) subscription.activated
# ======================================================
async def handle_subscription_activated(payload, db: AsyncSession):
    subscription = payload["payload"]["subscription"]["entity"]
    razorpay_subscription_id = subscription["id"]

    # Lookup existing payment
    payment = await db.scalar(
        select(Payment).where(Payment.reference_id == razorpay_subscription_id)
    )

    if not payment:
        return {"status": "ignored", "reason": "payment_not_found"}

    # Idempotent check
    existing = await db.scalar(
        select(Subscription).where(
            Subscription.user_id == payment.user_id,
            Subscription.status == "active"
        )
    )
    if existing:
        return {"status": "already_active"}

    plan = await db.scalar(select(Plan).where(Plan.id == payment.plan_id))
    if not plan:
        return {"status": "error", "detail": "plan_not_found"}

    now = ist_now_utc()
    ends = now + timedelta(days=30)
    grace = ends + timedelta(days=3)

    sub = Subscription(
        user_id=payment.user_id,
        plan_id=plan.id,
        payment_id=payment.id,
        status="active",
        starts_at=now,
        ends_at=ends,
        grace_ends_at=grace,
        is_trial=False,
        ai_campaign_limit_snapshot=plan.max_ai_campaigns,
        is_active=True,
    )

    db.add(sub)
    await db.commit()

    return {"status": "activated"}


# ======================================================
# 2) subscription.charged (RENEWAL)
# ======================================================
async def handle_subscription_charged(payload, db: AsyncSession):
    subscription = payload["payload"]["subscription"]["entity"]
    razorpay_subscription_id = subscription["id"]

    payment = await db.scalar(
        select(Payment).where(Payment.reference_id == razorpay_subscription_id)
    )

    if not payment:
        return {"status": "ignored"}

    # Find active subscription
    current_sub = await db.scalar(
        select(Subscription).where(
            Subscription.user_id == payment.user_id,
            Subscription.status == "active"
        )
    )

    # If none, treat as first activation fallback
    if not current_sub:
        return await handle_subscription_activated(payload, db)

    plan = await db.scalar(select(Plan).where(Plan.id == payment.plan_id))

    # Extend by 30 days
    current_sub.ends_at += timedelta(days=30)
    current_sub.grace_ends_at = current_sub.ends_at + timedelta(days=3)

    await db.commit()

    return {"status": "renewed"}


# ======================================================
# 3) invoice.paid (YEARLY SUBSCRIPTIONS + ADDONS + MANUAL)
# ======================================================
async def handle_invoice_paid(payload, db: AsyncSession):
    invoice = payload["payload"]["invoice"]["entity"]
    payment_id = invoice.get("payment_id")

    if not payment_id:
        return {"status": "ignored"}

    payment = await db.scalar(
        select(Payment).where(Payment.razorpay_payment_id == payment_id)
    )

    if not payment:
        return {"status": "ignored"}

    if payment.status == "paid":
        return {"status": "already_processed"}

    payment.status = "paid"
    payment.paid_at = ist_now_utc()

    await db.commit()

    return await finalize_payment(payment, db)


# ======================================================
# 4) payment.captured (NON-SUBSCRIPTION SINGLE CHARGES)
# ======================================================
async def handle_payment_captured(payload, db: AsyncSession):
    pay = payload["payload"]["payment"]["entity"]
    rp_payment_id = pay["id"]
    status = pay["status"]

    payment = await db.scalar(
        select(Payment).where(Payment.razorpay_payment_id == rp_payment_id)
    )

    if not payment:
        return {"status": "ignored"}

    if payment.status == "paid":
        return {"status": "already_processed"}

    payment.status = "paid"
    payment.paid_at = ist_now_utc()
    await db.commit()

    return await finalize_payment(payment, db)


# ======================================================
# 5) payment.failed
# ======================================================
async def handle_payment_failed(payload, db: AsyncSession):
    pay = payload["payload"]["payment"]["entity"]
    rp_payment_id = pay["id"]

    payment = await db.scalar(
        select(Payment).where(Payment.razorpay_payment_id == rp_payment_id)
    )

    if not payment:
        return {"status": "ignored"}

    payment.status = "failed"
    await db.commit()

    return {"status": "failed"}


# ======================================================
# FINAL PAYMENT HANDLER (ONE-TIME LOGIC)
# ======================================================
async def finalize_payment(payment: Payment, db: AsyncSession):
    """
    Handles:
    - yearly subscription purchase
    - manual buys
    - addons
    """

    now = ist_now_utc()

    # ========= YEARLY SUBSCRIPTION ==========
    if payment.payment_for == "subscription_yearly":
        plan = await db.scalar(select(Plan).where(Plan.id == payment.plan_id))
        if not plan:
            return {"status": "error", "reason": "plan_not_found"}

        # Year = 365 days (but calendar logic can be added later)
        # Grace = +3 days
        ends = now + timedelta(days=365)
        grace = ends + timedelta(days=3)

        # Expire old
        await db.execute(
            update(Subscription)
            .where(Subscription.user_id == payment.user_id)
            .values(status="expired", is_active=False)
        )

        sub = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            status="active",
            starts_at=now,
            ends_at=ends,
            grace_ends_at=grace,
            is_trial=False,
            ai_campaign_limit_snapshot=plan.max_ai_campaigns,
            is_active=True,
        )
        db.add(sub)

    # ========= MANUAL CAMPAIGN PURCHASE ==========
    elif payment.payment_for == "manual_campaign":
        # TODO: Campaign credits implementation later.
        pass

    # ========= ADDON PURCHASE ==========
    elif payment.payment_for == "addon":
        # TODO: Addon table implementation later.
        pass

    # Auto generate invoice (idempotent)
    inv = await db.scalar(select(Invoice).where(Invoice.payment_id == payment.id))
    if not inv:
        invoice = Invoice(
            user_id=payment.user_id,
            payment_id=payment.id,
            invoice_number=generate_invoice_no(),
            invoice_date=now,
            subtotal=payment.amount,
            tax_amount=0,
            total_amount=payment.amount,
            currency=payment.currency,
            status="paid",
        )
        db.add(invoice)

    await db.commit()
    return {"status": "processed"}

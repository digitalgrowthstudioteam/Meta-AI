import json
import hmac
import hashlib
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.core.config import settings
from app.billing.payment_models import Payment
from app.plans.subscription_models import Subscription
from app.plans.models import Plan


router = APIRouter(prefix="/billing/webhook", tags=["Billing Webhooks"])


# =====================================================
# RAZORPAY WEBHOOK (SOURCE OF TRUTH)
# =====================================================
@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay webhook handler.
    FINAL authority for payment + activation.
    """

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # -------------------------------------------------
    # VERIFY SIGNATURE
    # -------------------------------------------------
    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body.decode())
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    razorpay_order_id = entity.get("order_id")
    razorpay_payment_id = entity.get("id")
    status = entity.get("status")

    if not razorpay_order_id:
        return {"status": "ignored"}

    # -------------------------------------------------
    # FETCH PAYMENT (IDEMPOTENT)
    # -------------------------------------------------
    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        return {"status": "ignored"}

    if payment.status == "captured":
        return {"status": "already_processed"}

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = status

    if status != "captured":
        await db.commit()
        return {"status": "updated"}

    payment.paid_at = datetime.utcnow()

    # -------------------------------------------------
    # ACTIVATE BUSINESS OBJECT
    # -------------------------------------------------
    if payment.payment_for == "subscription":
        plan = await db.scalar(
            select(Plan).where(Plan.id == payment.related_reference_id)
        )
        if not plan:
            raise HTTPException(status_code=400, detail="Plan not found")

        starts_at = datetime.utcnow()
        ends_at = starts_at + timedelta(days=plan.validity_days)

        subscription = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            status="active",
            starts_at=starts_at,
            ends_at=ends_at,
            ai_campaign_limit_snapshot=plan.ai_campaign_limit,
            is_trial=False,
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(subscription)

    # future: manual_campaign / addon hooks

    await db.commit()
    return {"status": "activated"}

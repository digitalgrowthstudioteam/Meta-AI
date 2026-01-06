import json
import hmac
import hashlib
from datetime import datetime, timedelta
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.core.config import settings
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
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
    FINAL authority for payment + activation + invoice.
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
    period_from = None
    period_to = None

    if payment.payment_for == "subscription":
        plan = await db.scalar(
            select(Plan).where(Plan.id == payment.related_reference_id)
        )
        if not plan:
            raise HTTPException(status_code=400, detail="Plan not found")

        period_from = datetime.utcnow()
        period_to = period_from + timedelta(days=plan.validity_days)

        subscription = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            status="active",
            starts_at=period_from,
            ends_at=period_to,
            ai_campaign_limit_snapshot=plan.ai_campaign_limit,
            is_trial=False,
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(subscription)

    # -------------------------------------------------
    # CREATE INVOICE (IDEMPOTENT)
    # -------------------------------------------------
    existing_invoice = await db.scalar(
        select(Invoice).where(Invoice.payment_id == payment.id)
    )

    if not existing_invoice:
        invoice = Invoice(
            user_id=payment.user_id,
            payment_id=payment.id,
            invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            invoice_date=datetime.utcnow(),
            billing_name="Digital Growth Studio User",
            billing_email="billing@digitalgrowthstudio.in",
            subtotal=payment.amount,
            tax_amount=0,
            total_amount=payment.amount,
            currency=payment.currency,
            period_from=period_from,
            period_to=period_to,
            status="paid",
        )
        db.add(invoice)

    await db.commit()
    return {"status": "activated"}

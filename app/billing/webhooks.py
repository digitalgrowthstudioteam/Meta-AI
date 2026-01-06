import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.core.config import settings
from app.billing.payment_models import Payment


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
    This is the FINAL authority for payment status.
    """

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # -------------------------------------------------
    # VERIFY SIGNATURE
    # -------------------------------------------------
    import hmac
    import hashlib

    expected_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body.decode())
    event = payload.get("event")

    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_order_id = entity.get("order_id")
    razorpay_payment_id = entity.get("id")
    status = entity.get("status")

    if not razorpay_order_id:
        return {"status": "ignored"}

    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        return {"status": "ignored"}

    # -------------------------------------------------
    # APPLY STATUS (IMMUTABLE AFTER CAPTURE)
    # -------------------------------------------------
    if payment.status != "captured":
        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = status
        if status == "captured":
            payment.paid_at = datetime.utcnow()

        await db.commit()

    return {"status": "ok"}

import razorpay
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.billing.payment_models import Payment
from app.users.models import User


class BillingService:
    """
    Razorpay payment lifecycle service.

    RULES:
    - Order creation is idempotent
    - Webhook is source of truth
    - Client verification is secondary safety
    """

    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay keys not configured")

        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.public_key = settings.RAZORPAY_KEY_ID

    # =====================================================
    # CREATE RAZORPAY ORDER (IDEMPOTENT)
    # =====================================================
    async def create_order(
        self,
        *,
        db: AsyncSession,
        user: User,
        amount: int,
        payment_for: str,
        related_reference_id: UUID | None,
    ) -> Payment:
        """
        Creates Razorpay order + local payment record.
        Amount is in paise.
        """

        # Prevent duplicate open orders
        result = await db.execute(
            select(Payment).where(
                Payment.user_id == user.id,
                Payment.amount == amount,
                Payment.payment_for == payment_for,
                Payment.status == "created",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        order = self.client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1,
            }
        )

        payment = Payment(
            user_id=user.id,
            razorpay_order_id=order["id"],
            amount=amount,
            currency="INR",
            status="created",
            payment_for=payment_for,
            related_reference_id=related_reference_id,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    # =====================================================
    # VERIFY PAYMENT SIGNATURE (CLIENT CALLBACK)
    # =====================================================
    async def verify_payment(
        self,
        *,
        db: AsyncSession,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Payment:
        """
        Client-side verification.
        Webhook will still re-verify.
        """

        result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Payment record not found")

        if payment.status == "captured":
            return payment

        self.client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "captured"
        payment.paid_at = datetime.utcnow()

        await db.commit()
        await db.refresh(payment)
        return payment

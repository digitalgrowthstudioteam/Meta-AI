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

    🔒 RULES:
    - Order is created first
    - Payment is immutable after capture
    - Webhook is source of truth
    """

    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    # =====================================================
    # CREATE RAZORPAY ORDER
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
        Called after client-side payment success.
        """

        result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise ValueError("Payment record not found")

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

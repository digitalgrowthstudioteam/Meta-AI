import razorpay
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.users.models import User
from app.plans.subscription_models import Subscription
from app.plans.models import Plan
from app.admin.models_pricing import AdminPricingConfig


class BillingService:
    """
    Razorpay payment lifecycle + subscription activation service.

    RULES:
    - Order creation is idempotent
    - Payment verification is idempotent
    - Subscription activation happens HERE and ONLY HERE
    - Pricing, currency, tax are read from AdminPricingConfig
    """

    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay keys not configured")

        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.public_key = settings.RAZORPAY_KEY_ID

    # =====================================================
    # INTERNAL — LOAD ACTIVE PRICING CONFIG
    # =====================================================
    async def _get_active_pricing(self, db: AsyncSession) -> AdminPricingConfig:
        config = await db.scalar(
            select(AdminPricingConfig)
            .where(AdminPricingConfig.is_active.is_(True))
            .limit(1)
        )
        if not config:
            raise RuntimeError("No active pricing configuration")
        return config

    # =====================================================
    # PHASE-1: CREATE RECURRING SUBSCRIPTION (MONTHLY)
    # =====================================================
    async def create_subscription_recurring(
        self,
        *,
        db: AsyncSession,
        user: User,
        plan_id: int,
    ) -> Subscription:

        plan = await db.scalar(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            raise RuntimeError("Invalid or inactive plan")

        if not plan.auto_allowed:
            raise RuntimeError("Plan does not support auto billing")

        if not plan.razorpay_monthly_plan_id:
            raise RuntimeError("Missing Razorpay monthly plan mapping")

        # Create Razorpay subscription
        rp_sub = self.client.subscription.create(
            {
                "plan_id": plan.razorpay_monthly_plan_id,
                "customer_notify": 1,
                "quantity": 1,
                "total_count": 0,  # endless
            }
        )

        razorpay_subscription_id = rp_sub["id"]

        # Insert DB subscription as pending
        sub = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            status="pending",
            billing_cycle="monthly",
            razorpay_subscription_id=razorpay_subscription_id,
            starts_at=datetime.utcnow(),
            ends_at=None,
            is_active=False,
            is_trial=False,
            pricing_mode="standard",
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(sub)
        await db.commit()
        await db.refresh(sub)

        return sub

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
        related_reference_id: int | None,
    ) -> Payment:

        pricing = await self._get_active_pricing(db)

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
                "currency": pricing.currency,
                "payment_capture": 1,
            }
        )

        payment = Payment(
            user_id=user.id,
            razorpay_order_id=order["id"],
            amount=amount,
            currency=pricing.currency,
            status="created",
            payment_for=payment_for,
            related_reference_id=related_reference_id,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    # =====================================================
    # VERIFY PAYMENT + ACTIVATE SUBSCRIPTION
    # =====================================================
    async def verify_payment(
        self,
        *,
        db: AsyncSession,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Payment:

        payment = await db.scalar(
            select(Payment).where(
                Payment.razorpay_order_id == razorpay_order_id
            )
        )
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

        await self._activate_subscription_after_payment(
            db=db,
            payment=payment,
        )

        return payment

    # =====================================================
    # SUBSCRIPTION ACTIVATION (IDEMPOTENT)
    # =====================================================
    async def _activate_subscription_after_payment(
        self,
        *,
        db: AsyncSession,
        payment: Payment,
    ) -> None:

        if payment.payment_for != "subscription":
            return

        existing_sub = await db.scalar(
            select(Subscription).where(
                Subscription.payment_id == payment.id
            )
        )
        if existing_sub:
            return

        if payment.related_reference_id is None:
            raise RuntimeError("related_reference_id missing for subscription")

        plan = await db.scalar(
            select(Plan).where(
                Plan.id == payment.related_reference_id,
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            raise RuntimeError("Invalid or inactive plan")

        pricing = await self._get_active_pricing(db)

        now = datetime.utcnow()
        ends_at = now + timedelta(days=30)

        await db.execute(
            update(Subscription)
            .where(
                Subscription.user_id == payment.user_id,
                Subscription.status.in_(["trial", "active"]),
            )
            .values(
                status="expired",
                is_active=False,
                ends_at=now,
            )
        )

        subscription = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            status="active",
            starts_at=now,
            ends_at=ends_at,
            ai_campaign_limit_snapshot=plan.max_ai_campaigns or 0,
            is_active=True,
            is_trial=False,
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(subscription)

        tax_amount = int(
            payment.amount * pricing.tax_percentage / 100
        )

        invoice = Invoice(
            user_id=payment.user_id,
            payment_id=payment.id,
            invoice_number=f"{pricing.invoice_prefix}-{now.strftime('%Y%m%d')}-{payment.id.hex[:6].upper()}",
            invoice_date=now,
            subtotal=payment.amount,
            tax_amount=tax_amount,
            total_amount=payment.amount + tax_amount,
            currency=pricing.currency,
            period_from=now.date(),
            period_to=ends_at.date(),
            status="paid",
        )

        db.add(invoice)
        await db.commit()

# ================================
# app/billing/service.py (UNLIMITED SUBSCRIPTIONS)
# ================================

import razorpay
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
    def __init__(self):
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            raise RuntimeError("Razorpay keys not configured")

        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        self.public_key = settings.RAZORPAY_KEY_ID

    async def _get_active_pricing(self, db: AsyncSession) -> AdminPricingConfig:
        config = await db.scalar(
            select(AdminPricingConfig)
            .where(AdminPricingConfig.is_active.is_(True))
            .limit(1)
        )
        if not config:
            raise RuntimeError("No active pricing configuration")
        return config

    async def _resolve_plan_price(
        self,
        *,
        db: AsyncSession,
        plan: Plan,
        billing_cycle: str,
    ) -> int:
        plan_key = plan.name.lower()

        if plan_key == "free":
            raise RuntimeError("FREE plan cannot be purchased")

        if plan_key == "enterprise":
            raise RuntimeError("Enterprise pricing is manual only")

        pricing = await self._get_active_pricing(db)

        if plan_key not in pricing.plan_pricing:
            raise RuntimeError(f"No pricing configured for plan '{plan_key}'")

        p = pricing.plan_pricing[plan_key]

        if billing_cycle == "monthly":
            if "monthly_price" not in p:
                raise RuntimeError("Monthly price missing for plan")
            return p["monthly_price"]

        if billing_cycle == "yearly":
            if "yearly_price" not in p:
                raise RuntimeError("Yearly price missing for plan")
            return p["yearly_price"]

        raise RuntimeError("Invalid billing cycle")

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

        plan_key = plan.name.lower()

        if plan_key in ("free", "enterprise"):
            raise RuntimeError("Plan does not support recurring billing")

        if not plan.auto_allowed:
            raise RuntimeError("Plan has auto billing disabled")

        if not plan.razorpay_monthly_plan_id:
            raise RuntimeError("Missing Razorpay monthly plan mapping")

        rp_sub = self.client.subscription.create(
            {
                "plan_id": plan.razorpay_monthly_plan_id,
                "customer_notify": 1,
                "total_count": 1199,  # explicitly infinite billing
                "notes": {
                    "user_id": str(user.id),
                    "plan_id": str(plan.id),
                }
            }
        )

        razorpay_subscription_id = rp_sub["id"]

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

    async def create_order_manual_subscription(
        self,
        *,
        db: AsyncSession,
        user: User,
        plan_id: int,
        billing_cycle: str,
    ) -> Payment:

        plan = await db.scalar(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            raise RuntimeError("Invalid or inactive plan")

        amount = await self._resolve_plan_price(
            db=db,
            plan=plan,
            billing_cycle=billing_cycle,
        )

        pricing = await self._get_active_pricing(db)

        existing = await db.scalar(
            select(Payment).where(
                Payment.user_id == user.id,
                Payment.amount == amount,
                Payment.payment_for == f"subscription_{billing_cycle}",
                Payment.status == "created",
            )
        )
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
            plan_id=plan.id,
            razorpay_order_id=order["id"],
            amount=amount,
            currency=pricing.currency,
            status="created",
            payment_for=f"subscription_{billing_cycle}",
            mode="subscription",
            billing_cycle=billing_cycle,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment

    async def verify_payment(
        self,
        *,
        db: AsyncSession,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Payment:

        payment = await db.scalar(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
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

        await self._post_payment_subscription_logic(db=db, payment=payment)

        return payment

    async def _post_payment_subscription_logic(
        self,
        *,
        db: AsyncSession,
        payment: Payment,
    ) -> None:

        if payment.payment_for not in ("subscription_monthly", "subscription_yearly"):
            return

        if payment.plan_id is None:
            raise RuntimeError("plan_id missing in payment record")

        plan = await db.scalar(
            select(Plan).where(
                Plan.id == payment.plan_id,
                Plan.is_active.is_(True),
            )
        )
        if not plan:
            raise RuntimeError("Invalid or inactive plan")

        now = datetime.utcnow()
        if payment.payment_for == "subscription_monthly":
            ends_at = now + timedelta(days=30)
        else:
            ends_at = now + timedelta(days=365)

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

        sub = Subscription(
            user_id=payment.user_id,
            plan_id=plan.id,
            payment_id=payment.id,
            status="active",
            billing_cycle=payment.billing_cycle,
            starts_at=now,
            ends_at=ends_at,
            ai_campaign_limit_snapshot=plan.max_ai_campaigns or 0,
            is_active=True,
            is_trial=False,
            created_by_admin=False,
            assigned_by_admin=False,
        )

        db.add(sub)

        pricing = await self._get_active_pricing(db)
        gst = pricing.tax_percentage
        gst_amount = int(payment.amount * gst / 100)

        invoice = Invoice(
            user_id=payment.user_id,
            payment_id=payment.id,
            invoice_number=f"{pricing.invoice_prefix}-{now.strftime('%Y%m%d')}-{payment.id.hex[:6].upper()}",
            invoice_date=now,
            subtotal=payment.amount,
            tax_amount=gst_amount,
            total_amount=payment.amount + gst_amount,
            currency=pricing.currency,
            period_from=now.date(),
            period_to=ends_at.date(),
            status="paid",
        )

        db.add(invoice)
        await db.commit()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.plans.subscription_models import Subscription, SubscriptionAddon


router = APIRouter(prefix="/admin/billing-health", tags=["Admin Billing Health"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/overview")
async def billing_health_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    unpaid_payments = await db.scalar(
        select(func.count(Payment.id)).where(Payment.status != "paid")
    )

    unpaid_invoices = await db.scalar(
        select(func.count(Invoice.id)).where(Invoice.status != "paid")
    )

    expired_subs = await db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == "expired"
        )
    )

    active_addons = await db.scalar(
        select(func.count(SubscriptionAddon

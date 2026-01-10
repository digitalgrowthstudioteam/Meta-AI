from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.plans.subscription_models import Subscription, SubscriptionAddon


router = APIRouter(prefix="/admin/users", tags=["Admin User Billing"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/{user_id}/billing")
async def user_billing_snapshot(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    payments = await db.execute(
        select(Payment).where(Payment.user_id == user_id)
    )

    invoices = await db.execute(
        select(Invoice).where(Invoice.user_id == user_id)
    )

    subscription = await db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )

    addons = await db.execute(
        select(SubscriptionAddon)
        .where(SubscriptionAddon.user_id == user_id)
    )

    return {
        "subscription": (
            {
                "status": subscription.status,
                "ends_at": subscription.ends_at.isoformat()
                if subscription.ends_at
                else None,
                "ai_limit": subscription.ai_campaign_limit_snapshot,
            }
            if subscription
            else None
        ),
        "payments": [
            {
                "id": str(p.id),
                "amount": p.amount,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments.scalars().all()
        ],
        "invoices": [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "status": i.status,
                "created_at": i.created_at.isoformat(),
            }
            for i in invoices.scalars().all()
        ],
        "addons": [
            {
                "id": str(a.id),
                "slots": a.extra_ai_campaigns,
                "expires_at": a.expires_at.isoformat(),
            }
            for a in addons.scalars().all()
        ],
    }

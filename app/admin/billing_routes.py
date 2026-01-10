from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.plans.subscription_models import SubscriptionAddon

router = APIRouter(prefix="/admin/billing", tags=["Admin Billing"])

def require_admin(user: User):
if user.role != "admin":
raise HTTPException(status_code=403, detail="Admin access required")
return user

@router.get("/payments")
async def list_all_payments(
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)

result = await db.execute(
    select(Payment).order_by(Payment.created_at.desc())
)
payments = result.scalars().all()

return [
    {
        "id": str(p.id),
        "user_id": str(p.user_id),
        "amount": p.amount,
        "currency": p.currency,
        "status": p.status,
        "payment_for": p.payment_for,
        "created_at": p.created_at.isoformat(),
    }
    for p in payments
]


@router.get("/invoices")
async def list_all_invoices(
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)

result = await db.execute(
    select(Invoice).order_by(Invoice.created_at.desc())
)
invoices = result.scalars().all()

return [
    {
        "id": str(i.id),
        "user_id": str(i.user_id),
        "invoice_number": i.invoice_number,
        "amount": i.total_amount,
        "currency": i.currency,
        "status": i.status,
        "created_at": i.created_at.isoformat(),
        "download_url": f"/api/billing/invoices/{i.id}/download",
    }
    for i in invoices
]


@router.get("/slots")
async def list_all_slot_addons(
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)

result = await db.execute(
    select(SubscriptionAddon).order_by(SubscriptionAddon.created_at.desc())
)
slots = result.scalars().all()

return [
    {
        "id": str(s.id),
        "user_id": str(s.user_id),
        "extra_ai_campaigns": s.extra_ai_campaigns,
        "purchased_at": s.purchased_at.isoformat(),
        "expires_at": s.expires_at.isoformat(),
        "payment_id": str(s.payment_id) if s.payment_id else None,
    }
    for s in slots
]

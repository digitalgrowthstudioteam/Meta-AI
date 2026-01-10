from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice
from app.admin.models import AdminAuditLog


router = APIRouter(prefix="/admin/billing-timeline", tags=["Admin Billing"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/{user_id}")
async def billing_timeline(
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

    admin_logs = await db.execute(
        select(AdminAuditLog)
        .where(AdminAuditLog.target_id == user_id)
        .order_by(AdminAuditLog.created_at.desc())
    )

    events = []

    for p in payments.scalars():
        events.append(
            {
                "type": "payment",
                "at": p.created_at,
                "meta": {"amount": p.amount, "status": p.status},
            }
        )

    for i in invoices.scalars():
        events.append(
            {
                "type": "invoice",
                "at": i.created_at,
                "meta": {"invoice": i.invoice_number, "status": i.status},
            }
        )

    for l in admin_logs.scalars():
        events.append(
            {
                "type": "admin_action",
                "at": l.created_at,
                "meta": {"action": l.action, "reason": l.reason},
            }
        )

    events.sort(key=lambda x: x["at"], reverse=True)

    return events

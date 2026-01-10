from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice


router = APIRouter(prefix="/admin/revenue", tags=["Admin Revenue"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/sanity")
async def revenue_sanity_check(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    payment_sum = await db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(Payment.status == "paid")
    )

    invoice_sum = await db.scalar(
        select(func.coalesce(func.sum(Invoice.total_amount), 0))
        .where(Invoice.status == "paid")
    )

    return {
        "payments_total": payment_sum,
        "invoices_total": invoice_sum,
        "difference": payment_sum - invoice_sum,
        "status": "ok" if payment_sum == invoice_sum else "mismatch",
    }

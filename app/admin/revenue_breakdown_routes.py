from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment


router = APIRouter(prefix="/admin/revenue", tags=["Admin Revenue"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/by-source")
async def revenue_by_source(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(
            Payment.payment_for,
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
            func.count(Payment.id).label("count"),
        )
        .where(Payment.status == "paid")
        .group_by(Payment.payment_for)
    )

    return [
        {
            "source": r.payment_for,
            "amount": r.total,
            "payments": r.count,
        }
        for r in result.all()
    ]

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment


router = APIRouter(prefix="/admin/revenue", tags=["Admin Revenue"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/monthly")
async def monthly_revenue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(
            func.date_trunc("month", Payment.created_at).label("month"),
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
        )
        .where(Payment.status == "paid")
        .group_by(func.date_trunc("month", Payment.created_at))
        .order_by(func.date_trunc("month", Payment.created_at))
    )

    return [
        {
            "month": r.month.strftime("%Y-%m"),
            "total": r.total,
        }
        for r in result.all()
    ]

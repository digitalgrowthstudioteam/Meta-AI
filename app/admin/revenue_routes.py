from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, date

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.payment_models import Payment
from app.billing.invoice_models import Invoice


router = APIRouter(prefix="/admin/revenue", tags=["Admin Revenue"])


# =========================
# ADMIN GUARD
# =========================
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ==========================================================
# PHASE 7.19 — REVENUE SNAPSHOT (LIFETIME)
# ==========================================================
@router.get("/summary")
async def get_revenue_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.payment_for == "subscription", Payment.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("subscriptions"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.payment_for == "addon", Payment.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("addons"),
            func.count(Payment.id).label("payment_count"),
        ).where(Payment.status == "paid")
    )

    row = result.one()

    return {
        "currency": "INR",
        "total_revenue": row.total,
        "subscription_revenue": row.subscriptions,
        "addon_revenue": row.addons,
        "payments_count": row.payment_count,
    }


# ==========================================================
# PHASE 7.19 — DAILY REVENUE (RANGE)
# ==========================================================
@router.get("/daily")
async def get_daily_revenue(
    *,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    if start_date > end_date:
        raise HTTPException(400, "start_date must be <= end_date")

    stmt = (
        select(
            func.date(Payment.created_at).label("day"),
            func.coalesce(func.sum(Payment.amount), 0).label("total"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.payment_for == "subscription", Payment.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("subscriptions"),
            func.coalesce(
                func.sum(
                    case(
                        (Payment.payment_for == "addon", Payment.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("addons"),
        )
        .where(
            Payment.status == "paid",
            func.date(Payment.created_at) >= start_date,
            func.date(Payment.created_at) <= end_date,
        )
        .group_by(func.date(Payment.created_at))
        .order_by(func.date(Payment.created_at))
    )

    result = await db.execute(stmt)

    return [
        {
            "date": r.day.isoformat(),
            "total": r.total,
            "subscriptions": r.subscriptions,
            "addons": r.addons,
        }
        for r in result.all()
    ]


# ==========================================================
# PHASE 7.19 — INVOICE HEALTH SNAPSHOT
# ==========================================================
@router.get("/invoice-health")
async def get_invoice_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(
        select(
            func.count(Invoice.id).label("total"),
            func.count(
                case((Invoice.status == "paid", 1))
            ).label("paid"),
            func.count(
                case((Invoice.status == "cancelled", 1))
            ).label("cancelled"),
        )
    )

    row = result.one()

    return {
        "total_invoices": row.total,
        "paid_invoices": row.paid,
        "cancelled_invoices": row.cancelled,
    }

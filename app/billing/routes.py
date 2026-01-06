from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.service import BillingService
from app.billing.invoice_models import Invoice


router = APIRouter(prefix="/billing", tags=["Billing"])


# =====================================================
# CREATE RAZORPAY ORDER
# =====================================================
@router.post("/razorpay/order")
async def create_razorpay_order(
    *,
    amount: int = Query(..., gt=0, description="Amount in paise"),
    payment_for: str = Query(..., min_length=3),
    related_reference_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Creates a Razorpay order.
    """

    service = BillingService()

    try:
        payment = await service.create_order(
            db=db,
            user=current_user,
            amount=amount,
            payment_for=payment_for,
            related_reference_id=related_reference_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Unable to create payment order")

    return {
        "payment_id": str(payment.id),
        "razorpay_order_id": payment.razorpay_order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "key": service.public_key,
    }


# =====================================================
# VERIFY PAYMENT (CLIENT CALLBACK)
# =====================================================
@router.post("/razorpay/verify")
async def verify_razorpay_payment(
    *,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Client-side verification (webhook is source of truth).
    """

    service = BillingService()

    try:
        payment = await service.verify_payment(
            db=db,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Payment verification failed")

    return {
        "status": payment.status,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


# =====================================================
# LIST USER INVOICES
# =====================================================
@router.get("/invoices")
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Returns all invoices for the logged-in user.
    """

    result = await db.execute(
        select(Invoice)
        .where(Invoice.user_id == current_user.id)
        .order_by(Invoice.created_at.desc())
    )

    invoices = result.scalars().all()

    return [
        {
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "amount": inv.total_amount / 100,
            "currency": inv.currency,
            "status": inv.status,
            "period_from": inv.period_from.isoformat() if inv.period_from else None,
            "period_to": inv.period_to.isoformat() if inv.period_to else None,
            "created_at": inv.created_at.isoformat(),
            "download_url": inv.invoice_url,
        }
        for inv in invoices
    ]

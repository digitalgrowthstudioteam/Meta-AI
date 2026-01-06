from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.service import BillingService


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
    - Amount must be in paise
    - No subscription activation here
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
        "key": service.public_key,  # frontend needs this
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

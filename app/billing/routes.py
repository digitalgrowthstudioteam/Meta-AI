from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.service import BillingService
from app.billing.invoice_models import Invoice
from app.billing.invoice_service import InvoicePDFService


router = APIRouter(prefix="/billing", tags=["Billing"])


# =====================================================
# CREATE RAZORPAY ORDER
# =====================================================
@router.post("/razorpay/order")
async def create_razorpay_order(
    *,
    amount: int = Query(..., gt=0, description="Amount in paise"),
    payment_for: str = Query(..., min_length=3),
    related_reference_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Creates Razorpay order.
    Idempotent.
    """

    # Validate supported types (future-safe)
    allowed_types = {"subscription", "addon", "manual_campaign"}
    if payment_for not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid payment_for type")

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
        raise HTTPException(
            status_code=500,
            detail="Unable to create payment order",
        )

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
    Verifies Razorpay payment.
    Subscription activation happens inside BillingService.
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
        raise HTTPException(
            status_code=500,
            detail="Payment verification failed",
        )

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
            "amount": inv.total_amount,  # stored in paise
            "currency": inv.currency,
            "status": inv.status,
            "period_from": inv.period_from.isoformat() if inv.period_from else None,
            "period_to": inv.period_to.isoformat() if inv.period_to else None,
            "created_at": inv.created_at.isoformat(),
            "download_url": f"/api/billing/invoices/{inv.id}/download",
        }
        for inv in invoices
    ]


# =====================================================
# DOWNLOAD INVOICE PDF
# =====================================================
@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    pdf_bytes = InvoicePDFService.generate_pdf(invoice)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{invoice.invoice_number}.pdf"'
            )
        },
    )

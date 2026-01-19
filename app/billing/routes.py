from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.billing.service import BillingService
from app.billing.invoice_models import Invoice
from app.billing.invoice_service import InvoicePDFService
from app.admin.models_pricing import AdminPricingConfig
from app.plans.models import Plan
from app.plans.subscription_models import SubscriptionAddon


router = APIRouter(prefix="/billing", tags=["Billing"])


# =====================================================
# INTERNAL — LOAD ACTIVE PRICING CONFIG
# =====================================================
async def _get_active_pricing(db: AsyncSession) -> AdminPricingConfig:
    config = await db.scalar(
        select(AdminPricingConfig)
        .where(AdminPricingConfig.is_active.is_(True))
        .limit(1)
    )
    if not config:
        raise HTTPException(500, "No active pricing configuration")
    return config


# =====================================================
# PHASE-1: CREATE RAZORPAY SUBSCRIPTION (MONTHLY)
# =====================================================
@router.post("/razorpay/subscription/create")
async def create_razorpay_subscription(
    *,
    plan_id: int = Query(..., description="Plan ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    # Check plan exists
    plan = await db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.is_active.is_(True)
        )
    )
    if not plan:
        raise HTTPException(400, "Invalid or inactive plan")

    # Check auto billing eligibility
    if not plan.auto_allowed:
        raise HTTPException(400, "Plan does not support recurring billing")

    # Check Razorpay plan mapping
    if not plan.razorpay_monthly_plan_id:
        raise HTTPException(400, "Missing Razorpay monthly plan mapping for this plan")

    service = BillingService()

    # Create subscription via service
    try:
        payment = await service.create_subscription_recurring(
            db=db,
            user=current_user,
            plan_id=plan.id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "payment_id": str(payment.id),
        "razorpay_subscription_id": payment.razorpay_subscription_id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "billing_cycle": payment.billing_cycle,
        "key": service.public_key,
    }


# =====================================================
# CREATE RAZORPAY ORDER (ONE-TIME)
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
    allowed_types = {"subscription", "addon", "manual_campaign"}
    if payment_for not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid payment_for type")

    service = BillingService()

    payment = await service.create_order(
        db=db,
        user=current_user,
        amount=amount,
        payment_for=payment_for,
        related_reference_id=related_reference_id,
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
    service = BillingService()

    payment = await service.verify_payment(
        db=db,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )

    return {
        "status": payment.status,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


# =====================================================
# PURCHASE CAMPAIGN SLOTS (PRICING-DRIVEN)
# =====================================================
@router.post("/campaign-slots/buy")
async def buy_campaign_slots(
    *,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    pricing = await _get_active_pricing(db)

    packs = pricing.slot_packs.values()
    selected = next(
        (
            p for p in packs
            if quantity >= p["min_qty"]
            and (
                "max_qty" not in p
                or p["max_qty"] is None
                or quantity <= p["max_qty"]
            )
        ),
        None,
    )

    if not selected:
        raise HTTPException(400, "No pricing pack matches quantity")

    total_amount = selected["price"] * quantity

    service = BillingService()
    payment = await service.create_order(
        db=db,
        user=current_user,
        amount=total_amount,
        payment_for="addon",
        related_reference_id=None,
    )

    return {
        "payment_id": str(payment.id),
        "razorpay_order_id": payment.razorpay_order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "valid_days": selected["valid_days"],
    }


# =====================================================
# FINALIZE SLOT PURCHASE (POST-PAYMENT HOOK)
# =====================================================
@router.post("/campaign-slots/finalize")
async def finalize_campaign_slots(
    *,
    payment_id: UUID,
    quantity: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    pricing = await _get_active_pricing(db)

    packs = pricing.slot_packs.values()
    selected = next(
        (
            p for p in packs
            if quantity >= p["min_qty"]
            and (
                "max_qty" not in p
                or p["max_qty"] is None
                or quantity <= p["max_qty"]
            )
        ),
        None,
    )

    if not selected:
        raise HTTPException(400, "Invalid pricing pack")

    now = datetime.utcnow()
    expires_at = now + timedelta(days=selected["valid_days"])

    addon = SubscriptionAddon(
        user_id=current_user.id,
        subscription_id=None,
        extra_ai_campaigns=quantity,
        purchased_at=now,
        expires_at=expires_at,
        payment_id=payment_id,
    )

    db.add(addon)
    await db.commit()

    return {
        "status": "slots_added",
        "quantity": quantity,
        "expires_at": expires_at.isoformat(),
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
            "amount": inv.total_amount,
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
    invoice = await db.scalar(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.user_id == current_user.id,
        )
    )

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

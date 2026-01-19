# ================================
# app/billing/routes.py
# ================================

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
# INTERNAL — ACTIVE PRICING
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
# RECURRING MONTHLY SUBSCRIPTION (NON-ENTERPRISE)
# =====================================================
@router.post("/subscription/monthly/recurring")
async def create_recurring_subscription(
    *,
    plan_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    plan = await db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.is_active.is_(True)
        )
    )
    if not plan:
        raise HTTPException(400, "Invalid or inactive plan")

    plan_key = plan.name.lower()
    if plan_key == "free":
        raise HTTPException(400, "FREE plan cannot be purchased")

    if plan_key == "enterprise":
        raise HTTPException(400, "Enterprise is manual only")

    if not plan.auto_allowed:
        raise HTTPException(400, "Recurring billing disabled for this plan")

    if not plan.razorpay_monthly_plan_id:
        raise HTTPException(400, "Missing Razorpay mapping for recurring")

    service = BillingService()

    sub = await service.create_subscription_recurring(
        db=db,
        user=current_user,
        plan_id=plan.id,
    )

    return {
        "subscription_id": str(sub.id),
        "razorpay_subscription_id": sub.razorpay_subscription_id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "billing_cycle": sub.billing_cycle,
        "key": service.public_key,
    }


# =====================================================
# MANUAL MONTHLY SUBSCRIPTION (LOAD PRICE FROM ADMIN)
# =====================================================
@router.post("/subscription/monthly/manual")
async def create_manual_monthly_subscription(
    *,
    plan_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    plan = await db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.is_active.is_(True),
        )
    )
    if not plan:
        raise HTTPException(400, "Invalid or inactive plan")

    plan_key = plan.name.lower()
    if plan_key == "free":
        raise HTTPException(400, "FREE plan cannot be purchased")

    pricing = await _get_active_pricing(db)

    if plan_key not in pricing.plan_pricing:
        raise HTTPException(400, "Pricing not configured in admin")

    plan_price_config = pricing.plan_pricing[plan_key]
    if "monthly" not in plan_price_config:
        raise HTTPException(400, "Monthly price not configured for this plan")

    amount = int(plan_price_config["monthly"])  # paise

    service = BillingService()
    payment = await service.create_order(
        db=db,
        user=current_user,
        amount=amount,
        payment_for="subscription_monthly",
        related_reference_id=plan.id,
    )

    return {
        "payment_id": str(payment.id),
        "razorpay_order_id": payment.razorpay_order_id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "billing_cycle": "monthly",
        "amount": amount,
        "currency": pricing.currency,
        "key": service.public_key,
    }


# =====================================================
# MANUAL YEARLY SUBSCRIPTION (LOAD PRICE FROM ADMIN)
# =====================================================
@router.post("/subscription/yearly/manual")
async def create_manual_yearly_subscription(
    *,
    plan_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    plan = await db.scalar(
        select(Plan).where(
            Plan.id == plan_id,
            Plan.is_active.is_(True),
        )
    )
    if not plan:
        raise HTTPException(400, "Invalid or inactive plan")

    plan_key = plan.name.lower()
    if plan_key == "free":
        raise HTTPException(400, "FREE plan cannot be purchased")

    pricing = await _get_active_pricing(db)

    if plan_key not in pricing.plan_pricing:
        raise HTTPException(400, "Pricing not configured in admin")

    plan_price_config = pricing.plan_pricing[plan_key]
    if "yearly" not in plan_price_config:
        raise HTTPException(400, "Yearly price not configured for this plan")

    amount = int(plan_price_config["yearly"])  # paise

    service = BillingService()
    payment = await service.create_order(
        db=db,
        user=current_user,
        amount=amount,
        payment_for="subscription_yearly",
        related_reference_id=plan.id,
    )

    return {
        "payment_id": str(payment.id),
        "razorpay_order_id": payment.razorpay_order_id,
        "plan_id": plan.id,
        "plan_name": plan.name,
        "billing_cycle": "yearly",
        "amount": amount,
        "currency": pricing.currency,
        "key": service.public_key,
    }


# =====================================================
# VERIFY PAYMENT (MANUAL)
# =====================================================
@router.post("/razorpay/verify")
async def verify_manual_payment(
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
    return {"status": payment.status}


# =====================================================
# CAMPAIGN SLOT PURCHASE (UNCHANGED)
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
        (p for p in packs if quantity >= p["min_qty"]
         and ("max_qty" not in p or p["max_qty"] is None or quantity <= p["max_qty"])),
        None,
    )
    if not selected:
        raise HTTPException(400, "Invalid slot quantity")

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
        "amount": total_amount,
        "currency": pricing.currency,
        "valid_days": selected["valid_days"],
    }


# =====================================================
# FINALIZE SLOTS (POST PAYMENT)
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
        (p for p in packs if quantity >= p["min_qty"]
         and ("max_qty" not in p or p["max_qty"] is None or quantity <= p["max_qty"])),
        None,
    )
    if not selected:
        raise HTTPException(400, "Invalid pack")

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

    return {"status": "slots_added", "expires_at": expires_at.isoformat()}


# =====================================================
# INVOICES
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
        raise HTTPException(404, "Invoice not found")

    pdf_bytes = InvoicePDFService.generate_pdf(invoice)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'},
    )

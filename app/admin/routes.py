from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign
from app.plans.subscription_models import Subscription
from app.campaigns.models import CampaignActionLog

# -------------------------
# Admin Schemas / Services
# -------------------------
from app.admin.schemas import (
    AdminOverrideCreate,
    AdminOverrideResponse,
)
from app.admin.service import AdminOverrideService

# -------------------------
# Plan / Subscription Enforcement
# -------------------------
from app.plans.enforcement import PlanEnforcementService

# -------------------------
# Metrics / AI Services
# -------------------------
from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)
from app.ai_engine.aggregation_engine.campaign_aggregation_service import (
    CampaignAggregationService,
)
from app.billing.invoice_service import InvoiceService
from app.billing.service import BillingService

# -------------------------
# Metrics Sync (already wired)
# -------------------------
from app.admin.metrics_sync_routes import router as metrics_sync_router


router = APIRouter(prefix="/admin", tags=["Admin"])


# =========================
# ADMIN GUARD
# =========================
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# ADMIN DASHBOARD
# =========================
@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminOverrideService.get_dashboard_stats(db=db)


# =========================
# ADMIN USERS (READ ONLY)
# =========================
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    response = []

    for u in users:
        sub_status = await db.scalar(
            select(Subscription.status)
            .where(Subscription.user_id == u.id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )

        ai_campaigns = await db.scalar(
            select(func.count(Campaign.id))
            .where(
                Campaign.user_id == u.id,
                Campaign.ai_active.is_(True),
            )
        )

        response.append(
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login_at": (
                    u.last_login_at.isoformat()
                    if getattr(u, "last_login_at", None)
                    else None
                ),
                "subscription_status": sub_status,
                "ai_campaigns_active": ai_campaigns or 0,
            }
        )

    return response


# ==========================================================
# PHASE 3.2 — SUPPORT TOOLS (AUDITED, REASON REQUIRED)
# ==========================================================

async def _log_support_action(
    *,
    db: AsyncSession,
    admin_user: User,
    target_user_id: UUID,
    action: str,
    reason: str,
):
    db.add(
        CampaignActionLog(
            campaign_id=None,
            user_id=admin_user.id,
            actor_type="admin",
            action_type=action,
            reason=reason,
            before_state={"target_user_id": str(target_user_id)},
            after_state={},
            created_at=datetime.utcnow(),
        )
    )
    await db.commit()


@router.post("/support/force_meta_resync")
async def force_meta_resync(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await CampaignDailyMetricsSyncService.force_user_resync(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="force_meta_resync",
        reason=reason,
    )

    return {"status": "ok"}


@router.post("/support/refresh_billing")
async def refresh_billing_from_razorpay(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await BillingService.refresh_user_billing(db=db, user_id=user_id)

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="refresh_billing_from_razorpay",
        reason=reason,
    )

    return {"status": "ok"}


@router.post("/support/clear_ai_queue")
async def clear_ai_queue(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await CampaignAggregationService.clear_user_queue(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="clear_ai_queue",
        reason=reason,
    )

    return {"status": "ok"}


@router.post("/support/reprocess_webhooks")
async def reprocess_webhooks(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await BillingService.reprocess_failed_webhooks(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="reprocess_razorpay_webhooks",
        reason=reason,
    )

    return {"status": "ok"}


@router.post("/support/regenerate_invoices")
async def regenerate_invoices(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await InvoiceService.regenerate_user_invoices(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="regenerate_invoice_pdfs",
        reason=reason,
    )

    return {"status": "ok"}


@router.post("/support/rebuild_ml")
async def rebuild_ml_aggregations(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    user_id = UUID(payload["user_id"])
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    await CampaignAggregationService.rebuild_user_aggregations(
        db=db, user_id=user_id
    )

    await _log_support_action(
        db=db,
        admin_user=current_user,
        target_user_id=user_id,
        action="rebuild_ml_aggregations",
        reason=reason,
    )

    return {"status": "ok"}


# =========================
# METRICS SYNC ROUTES
# =========================
router.include_router(metrics_sync_router)

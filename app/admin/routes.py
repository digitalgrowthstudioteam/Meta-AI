from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.plans.subscription_models import Subscription

# -------------------------
# Admin Schemas / Services
# -------------------------
from app.admin.schemas import (
    AdminOverrideCreate,
    AdminOverrideResponse,
)
from app.admin.service import AdminOverrideService

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
# PHASE 5 — ADMIN CAMPAIGN EXPLORER (READ)
# ==========================================================
@router.get("/campaigns")
async def admin_list_campaigns(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
    user_id: UUID | None = Query(None),
    ai_active: bool | None = Query(None),
):
    require_admin(current_user)

    stmt = select(Campaign)

    if user_id:
        stmt = stmt.where(Campaign.user_id == user_id)

    if ai_active is not None:
        stmt = stmt.where(Campaign.ai_active.is_(ai_active))

    result = await db.execute(stmt.order_by(Campaign.created_at.desc()))
    campaigns = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "user_id": str(c.user_id),
            "name": c.name,
            "objective": c.objective,
            "status": c.status,
            "ai_active": c.ai_active,
            "ai_execution_locked": c.ai_execution_locked,
            "is_manual": c.is_manual,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


# ==========================================================
# PHASE 5 — FORCE AI ENABLE / DISABLE (AUDITED)
# ==========================================================
@router.post("/campaigns/{campaign_id}/force-ai")
async def admin_force_ai_toggle(
    campaign_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    enable = payload.get("enable")
    reason = payload.get("reason")

    if enable is None or not reason:
        raise HTTPException(400, "enable and reason required")

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    before_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    campaign.ai_active = bool(enable)
    campaign.ai_execution_locked = False if enable else True
    campaign.ai_activated_at = datetime.utcnow() if enable else None
    campaign.ai_deactivated_at = None if enable else datetime.utcnow()

    after_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    db.add(
        CampaignActionLog(
            campaign_id=campaign.id,
            user_id=current_user.id,
            actor_type="admin",
            action_type="force_ai_toggle",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()

    return {"status": "ok", "campaign_id": str(campaign.id), "ai_active": campaign.ai_active}


# ==========================================================
# PHASE 5 — RESET BENCHMARKS / MARK INCOMPATIBLE
# ==========================================================
@router.post("/campaigns/{campaign_id}/reset")
async def admin_reset_campaign_state(
    campaign_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "reason required")

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    before_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    campaign.ai_active = False
    campaign.ai_execution_locked = True
    campaign.ai_activated_at = None
    campaign.ai_deactivated_at = datetime.utcnow()

    after_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    db.add(
        CampaignActionLog(
            campaign_id=campaign.id,
            user_id=current_user.id,
            actor_type="admin",
            action_type="reset_campaign_ai_state",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()
    return {"status": "ok", "campaign_id": str(campaign.id)}


# ==========================================================
# PHASE 3.2 — SUPPORT TOOLS (UNCHANGED)
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

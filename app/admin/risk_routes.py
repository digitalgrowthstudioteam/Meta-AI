from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.plans.subscription_models import Subscription
from app.billing.payment_models import Payment
from app.admin.models import AdminAuditLog

router = APIRouter(prefix="/admin/risk", tags=["Admin Risk"])


def require_admin(user: User):
    if user.role != "admin":
        raise PermissionError("Admin access required")
    return user


# ==========================================================
# PHASE 8.2 — RISK SUMMARY (UNCHANGED)
# ==========================================================
@router.get("/summary")
async def get_risk_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)

    failed_payments = await db.scalar(
        select(func.count(Payment.id)).where(
            and_(
                Payment.status == "failed",
                Payment.created_at >= last_7d,
            )
        )
    )

    expired_subs = await db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == "expired"
        )
    )

    ai_locked_active = await db.scalar(
        select(func.count(Campaign.id)).where(
            and_(
                Campaign.ai_active.is_(True),
                Campaign.ai_execution_locked.is_(True),
            )
        )
    )

    frequent_ai_toggles = await db.scalar(
        select(func.count(CampaignActionLog.id)).where(
            and_(
                CampaignActionLog.action_type == "ai_toggle",
                CampaignActionLog.created_at >= last_7d,
            )
        )
    )

    stale_meta_sync = await db.scalar(
        select(func.count(Campaign.id)).where(
            Campaign.last_meta_sync_at < (now - timedelta(days=2))
        )
    )

    return {
        "users": {
            "failed_payments_7d": failed_payments or 0,
            "expired_subscriptions": expired_subs or 0,
        },
        "campaigns": {
            "ai_active_but_locked": ai_locked_active or 0,
            "ai_toggle_events_7d": frequent_ai_toggles or 0,
        },
        "system": {
            "stale_meta_sync_campaigns": stale_meta_sync or 0,
        },
        "generated_at": now.isoformat(),
    }


# ==========================================================
# PHASE 8.4 — RISK TIMELINE (READ-ONLY)
# ==========================================================
@router.get("/timeline")
async def get_risk_timeline(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
    limit: int = 50,
):
    require_admin(current_user)

    events: list[dict] = []

    # -------------------------
    # ADMIN RISK ACTIONS
    # -------------------------
    admin_logs = await db.execute(
        select(AdminAuditLog)
        .where(AdminAuditLog.action.like("risk_%"))
        .order_by(desc(AdminAuditLog.created_at))
        .limit(limit)
    )

    for log in admin_logs.scalars().all():
        events.append(
            {
                "id": str(log.id),
                "source": "ADMIN",
                "action": log.action,
                "target_id": str(log.target_id) if log.target_id else None,
                "reason": log.reason,
                "timestamp": log.created_at.isoformat(),
            }
        )

    # -------------------------
    # CAMPAIGN AI / SYSTEM EVENTS
    # -------------------------
    campaign_logs = await db.execute(
        select(CampaignActionLog)
        .order_by(desc(CampaignActionLog.created_at))
        .limit(limit)
    )

    for log in campaign_logs.scalars().all():
        events.append(
            {
                "id": str(log.id),
                "source": log.actor_type.upper(),
                "action": log.action_type,
                "target_id": str(log.campaign_id),
                "reason": log.reason,
                "timestamp": log.created_at.isoformat(),
            }
        )

    # -------------------------
    # BILLING FAILURE EVENTS (DERIVED)
    # -------------------------
    failed_payments = await db.execute(
        select(Payment)
        .where(Payment.status == "failed")
        .order_by(desc(Payment.created_at))
        .limit(limit)
    )

    for p in failed_payments.scalars().all():
        events.append(
            {
                "id": str(p.id),
                "source": "BILLING",
                "action": "payment_failed",
                "target_id": str(p.user_id),
                "reason": None,
                "timestamp": p.created_at.isoformat(),
            }
        )

    # -------------------------
    # SORT & RETURN
    # -------------------------
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    return events[:limit]

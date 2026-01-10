from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.plans.subscription_models import Subscription
from app.billing.payment_models import Payment

router = APIRouter(prefix="/admin/risk", tags=["Admin Risk"])


def require_admin(user: User):
    if user.role != "admin":
        raise PermissionError("Admin access required")
    return user


@router.get("/summary")
async def get_risk_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    now = datetime.utcnow()
    last_7d = now - timedelta(days=7)

    # -------------------------
    # USER RISK SIGNALS
    # -------------------------
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

    # -------------------------
    # CAMPAIGN RISK SIGNALS
    # -------------------------
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

    # -------------------------
    # SYSTEM RISK SIGNALS
    # -------------------------
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

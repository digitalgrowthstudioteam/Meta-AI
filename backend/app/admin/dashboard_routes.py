from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_admin
from app.users.models import User
from app.campaigns.models import Campaign

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/dashboard/summary")
async def admin_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    users_count = await db.execute(select(func.count(User.id)))
    users_count = users_count.scalar() or 0

    active_subs = 0
    expired_subs = 0

    campaigns_total = await db.execute(select(func.count(Campaign.id)))
    campaigns_total = campaigns_total.scalar() or 0

    ai_active = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.ai_active.is_(True))
    )
    ai_active = ai_active.scalar() or 0

    manual = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.is_manual.is_(True))
    )
    manual = manual.scalar() or 0

    return {
        "users": users_count,
        "subscriptions": {
            "active": active_subs,
            "expired": expired_subs,
        },
        "campaigns": {
            "total": campaigns_total,
            "ai_active": ai_active,
            "manual": manual,
        },
        "last_activity": datetime.utcnow().isoformat(),
        "system_status": "ok",
    }

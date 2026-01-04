"""
Admin Routes — Campaign Daily Metrics Sync

Purpose:
- Manually trigger Meta Insights → DB sync
- Used only for Phase 6.5 verification
- No scheduler, no cron
"""

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)

router = APIRouter(prefix="/admin/metrics", tags=["Admin Metrics"])


@router.post("/sync-daily")
async def sync_campaign_daily_metrics(
    target_date: date = Query(..., description="Date to sync (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Manually sync campaign daily metrics for a given date.
    """
    # 🔒 Safety: admin-only usage (simple guard for now)
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = CampaignDailyMetricsSyncService(db)
    await service.sync_for_date(target_date)

    return {
        "status": "success",
        "message": f"Campaign daily metrics synced for {target_date}",
    }

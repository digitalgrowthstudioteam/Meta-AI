"""
Admin Routes — Campaign Daily Metrics Sync

Purpose:
- Manually trigger Meta Insights → DB sync
- Used only for Phase 6.5 verification
- No scheduler, no cron
"""

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)

router = APIRouter(prefix="/metrics", tags=["Admin Metrics"])


@router.post("/sync-daily", status_code=status.HTTP_200_OK)
async def sync_campaign_daily_metrics(
    target_date: date = Query(..., description="Date to sync (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    """
    Manually sync campaign daily metrics for a given date.
    Idempotent by design — safe to re-run.
    """

    # 🔒 Admin-only guard
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    service = CampaignDailyMetricsSyncService(db)

    try:
        result = await service.sync_for_date(target_date)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Metrics sync failed: {str(exc)}",
        )

    return {
        "status": "success",
        "target_date": str(target_date),
        "synced_campaigns": result.get("synced_campaigns", 0),
        "skipped_campaigns": result.get("skipped_campaigns", 0),
        "failed_campaigns": result.get("failed_campaigns", 0),
    }

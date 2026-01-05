"""
Admin Metrics Routes

PHASE 6.5 — MANUAL METRICS INGESTION

Admin-only endpoints to trigger Meta Insights sync.
READ-ONLY Meta
SAFE to retry
"""

from datetime import date
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_admin_user
from app.meta_insights.services.campaign_daily_metrics_sync_service import (
    CampaignDailyMetricsSyncService,
)

router = APIRouter(
    prefix="/admin/metrics",
    tags=["Admin Metrics"],
)


# =====================================================
# MANUAL DAILY METRICS SYNC
# =====================================================
@router.post("/sync-daily")
async def sync_daily_campaign_metrics(
    *,
    target_date: date = Query(..., description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin_user),
):
    """
    Triggers daily Meta Insights ingestion.

    - Idempotent
    - Safe to retry
    - Admin-only
    """

    service = CampaignDailyMetricsSyncService(db)
    result = await service.sync_for_date(target_date)

    return {
        "status": "ok",
        "target_date": target_date,
        **result,
    }

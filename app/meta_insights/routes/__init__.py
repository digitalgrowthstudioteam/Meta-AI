from fastapi import APIRouter

from .admin_metrics_routes import router as admin_metrics_router
from app.meta_insights.routes.audience_insights_routes import (
    router as audience_insights_router,
)

router = APIRouter()

# Audience / Breakdown Insights (Phase 8)
router.include_router(audience_insights_router)

# Admin Daily Metrics Sync (Phase 6.5)
router.include_router(admin_metrics_router)

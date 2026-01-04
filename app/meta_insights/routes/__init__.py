"""
Meta Insights Routes Package

Purpose:
- Central router for all Meta Insights read APIs
- Phase 6.5: Metrics
- Phase 8: Audience / Breakdown Insights
"""

from fastapi import APIRouter

from app.meta_insights.routes.audience_insights_routes import (
    router as audience_insights_router,
)

router = APIRouter()

# -------------------------------------------------
# Audience / Breakdown Insights (Phase 8)
# -------------------------------------------------
router.include_router(audience_insights_router)

from fastapi import APIRouter

from app.ai_engine.routes.actions import router as actions_router
from app.ai_engine.routes.category_insights_routes import router as category_router
from app.ai_engine.routes.audience_insights_routes import router as audience_insights_router


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

# AI actions (suggestions, approvals, feedback)
router.include_router(actions_router)

# Category-level global insights
router.include_router(category_router)

# Audience insights (campaign-level breakdowns)
router.include_router(audience_insights_router)

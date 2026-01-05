from fastapi import APIRouter

from app.ai_engine.routes.actions import router as actions_router
from app.ai_engine.routes.category_insights_routes import router as category_router
from .audience_insights_routes import router as audience_insights_router


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)

router.include_router(actions_router)
router.include_router(category_router)

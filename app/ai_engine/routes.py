from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import AIActionSet

# 🔥 IMPORT CATEGORY INSIGHTS ROUTES
from app.ai_engine.routes.category_insights_routes import (
    router as category_insights_router,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

# -----------------------------------------------------
# AI ACTIONS (PHASE 7)
# -----------------------------------------------------
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    runner = AIDecisionRunner()
    return await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

# -----------------------------------------------------
# CATEGORY INSIGHTS (PHASE 9.5)
# -----------------------------------------------------
router.include_router(category_insights_router)

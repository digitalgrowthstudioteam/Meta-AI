from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import get_session_context

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import AIActionSet

# 🔥 CATEGORY INSIGHTS
from app.ai_engine.routes.category_insights_routes import (
    router as category_insights_router,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

# -----------------------------------------------------
# AI ACTIONS — STRICT SESSION CONTEXT (LOCKED)
# -----------------------------------------------------
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    db: AsyncSession = Depends(get_db),
    session: dict = Depends(get_session_context),
):
    """
    AI Actions
    - STRICT selected ad account only
    - ZERO user-wide leakage
    """

    ad_account = session["ad_account"]

    if not ad_account:
        return []

    runner = AIDecisionRunner()
    return await runner.run_for_ad_account(
        db=db,
        ad_account_id=UUID(ad_account["id"]),
    )


# -----------------------------------------------------
# CATEGORY INSIGHTS (PHASE 9.5 — SESSION SAFE)
# -----------------------------------------------------
router.include_router(category_insights_router)

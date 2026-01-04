from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import AIActionSet


router = APIRouter(
    prefix="/ai",
    tags=["AI Suggestions"],
)


# =====================================================
# LIVE AI SUGGESTIONS (NO DB — PHASE 7 MODE)
# =====================================================
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    LIVE AI suggestions for dashboard.

    - Computed on demand
    - NOT persisted
    - SAFE
    - Correct for Phase 7
    """

    runner = AIDecisionRunner()

    return await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

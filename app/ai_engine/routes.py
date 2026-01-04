from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import DecisionRunner
from app.ai_engine.models.action_models import AIActionSet


router = APIRouter(
    prefix="/ai",
    tags=["AI Suggestions"],
)


# =====================================================
# LIVE AI SUGGESTIONS (SUGGEST-ONLY)
# =====================================================
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    Returns LIVE AI suggestions for the logged-in user.

    Characteristics:
    - Computed on demand
    - NOT persisted
    - Suggest-only
    - Safe for dashboard polling
    """

    runner = DecisionRunner()

    action_sets = await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

    return action_sets

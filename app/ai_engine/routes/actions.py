from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import AIActionSet


router = APIRouter(
    prefix="/actions",
    tags=["AI Actions"],
)


@router.get("", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    LIVE AI suggestions (read-only)

    SAFE:
    - No DB writes
    - No Meta mutations
    - Safe for polling
    """

    runner = AIDecisionRunner()
    return await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

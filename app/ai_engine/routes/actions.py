from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import (
    AIActionSet,
    ActionApprovalStatus,
)

# 🔥 CATEGORY INSIGHTS
from app.ai_engine.routes.category_insights_routes import (
    router as category_insights_router,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

# -----------------------------------------------------
# AI ACTIONS — PHASE 11 (APPROVAL ENFORCED)
# -----------------------------------------------------
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    """
    SAFE AI suggestions with hard approval enforcement.

    - Non-approved actions are NEVER executable
    - Auto-execution is impossible by design
    """

    runner = AIDecisionRunner()
    action_sets = await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

    # -------------------------------------------------
    # PHASE 11 — HARD APPROVAL FILTER
    # -------------------------------------------------
    filtered_sets: List[AIActionSet] = []

    for action_set in action_sets:
        approved_actions = []

        for action in action_set.actions:
            if (
                action.auto_execution_blocked
                and action.requires_human_approval
                and action.approval_status == ActionApprovalStatus.APPROVED
            ):
                approved_actions.append(action)

            # Always allow NO_ACTION (insight-only)
            if action.action_type.value == "NO_ACTION":
                approved_actions.append(action)

        if approved_actions:
            filtered_sets.append(
                AIActionSet(
                    campaign_id=action_set.campaign_id,
                    actions=approved_actions,
                )
            )

    return filtered_sets


# -----------------------------------------------------
# CATEGORY INSIGHTS (PHASE 9.5)
# -----------------------------------------------------
router.include_router(category_insights_router)

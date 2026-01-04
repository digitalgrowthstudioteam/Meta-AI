from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import (
    AIActionSet,
    ActionApprovalStatus,
)

from app.ai_engine.models.ai_action_feedback import AIActionFeedback

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
    runner = AIDecisionRunner()
    action_sets = await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

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
# APPROVE AI ACTION (PHASE 11)
# -----------------------------------------------------
@router.post("/actions/{action_id}/approve", status_code=200)
async def approve_ai_action(
    *,
    action_id,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    stmt = select(AIActionFeedback).where(
        AIActionFeedback.id == action_id
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.approval_status != ActionApprovalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action cannot be approved in current state",
        )

    action.approval_status = ActionApprovalStatus.APPROVED
    action.approved_by_user_id = user.id
    action.approved_at = datetime.utcnow()

    await db.commit()
    return {"status": "approved"}


# -----------------------------------------------------
# REJECT AI ACTION (PHASE 11)
# -----------------------------------------------------
@router.post("/actions/{action_id}/reject", status_code=200)
async def reject_ai_action(
    *,
    action_id,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    stmt = select(AIActionFeedback).where(
        AIActionFeedback.id == action_id
    )
    result = await db.execute(stmt)
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.approval_status not in (
        ActionApprovalStatus.DRAFT,
        ActionApprovalStatus.PENDING_APPROVAL,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action cannot be rejected in current state",
        )

    action.approval_status = ActionApprovalStatus.REJECTED
    action.approved_by_user_id = user.id
    action.approved_at = datetime.utcnow()

    await db.commit()
    return {"status": "rejected"}


# -----------------------------------------------------
# CATEGORY INSIGHTS (PHASE 9.5)
# -----------------------------------------------------
router.include_router(category_insights_router)

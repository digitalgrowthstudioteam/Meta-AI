from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.meta_api.models import MetaAdAccount, UserMetaAdAccount
from app.campaigns.models import Campaign

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import (
    AIActionSet,
    ActionApprovalStatus,
)
from app.ai_engine.models.ai_action_feedback import AIActionFeedback

from app.ai_engine.routes.category_insights_routes import (
    router as category_insights_router,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

# -----------------------------------------------------
# AI ACTIONS — STRICT USER + SELECTED AD ACCOUNT
# -----------------------------------------------------
@router.get("/actions", response_model=List[AIActionSet])
async def list_ai_actions(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    # 🔒 resolve selected ad account
    stmt = (
        select(MetaAdAccount.id)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.is_selected.is_(True),
        )
    )
    result = await db.execute(stmt)
    selected_ad_account_id = result.scalar_one_or_none()

    if not selected_ad_account_id:
        return []

    # 🔒 fetch campaigns only for selected ad account
    stmt = select(Campaign.id).where(
        Campaign.ad_account_id == selected_ad_account_id,
        Campaign.is_archived.is_(False),
    )
    result = await db.execute(stmt)
    allowed_campaign_ids = {row[0] for row in result.all()}

    if not allowed_campaign_ids:
        return []

    # run AI engine
    runner = AIDecisionRunner()
    action_sets = await runner.run_for_user(
        db=db,
        user_id=user.id,
    )

    filtered_sets: List[AIActionSet] = []

    for action_set in action_sets:
        if action_set.campaign_id not in allowed_campaign_ids:
            continue

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
# APPROVE AI ACTION
# -----------------------------------------------------
@router.post("/actions/{action_id}/approve", status_code=200)
async def approve_ai_action(
    *,
    action_id,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    stmt = select(AIActionFeedback).where(
        AIActionFeedback.id == action_id,
        AIActionFeedback.user_id == user.id,
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
# REJECT AI ACTION
# -----------------------------------------------------
@router.post("/actions/{action_id}/reject", status_code=200)
async def reject_ai_action(
    *,
    action_id,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
):
    stmt = select(AIActionFeedback).where(
        AIActionFeedback.id == action_id,
        AIActionFeedback.user_id == user.id,
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
# CATEGORY INSIGHTS
# -----------------------------------------------------
router.include_router(category_insights_router)

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.auth.dependencies import get_session_context, require_user
from app.users.models import User

from app.ai_engine.decision_engine.decision_runner import AIDecisionRunner
from app.ai_engine.models.action_models import AIActionSet
from app.ai_engine.models.ml_action_outcomes import MLActionOutcome
from app.ai_engine.models.ml_campaign_features import MLCampaignFeatures

# 🔥 CATEGORY INSIGHTS
from app.ai_engine.routes.category_insights_routes import (
    router as category_insights_router,
)

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# =========================
# ADMIN GUARD (LOCAL, SAFE)
# =========================
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# -----------------------------------------------------
# USER AI ACTIONS — SESSION LOCKED (UNCHANGED)
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
# ADMIN — AI INTELLIGENCE PANEL (PHASE 2.3, READ-ONLY)
# -----------------------------------------------------
@router.get("/admin/overview")
async def admin_ai_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    total_actions = await db.scalar(
        select(func.count(MLActionOutcome.id))
    )

    success_actions = await db.scalar(
        select(func.count(MLActionOutcome.id))
        .where(MLActionOutcome.status == "success")
    )

    failed_actions = await db.scalar(
        select(func.count(MLActionOutcome.id))
        .where(MLActionOutcome.status == "failed")
    )

    avg_confidence = await db.scalar(
        select(func.avg(MLCampaignFeatures.confidence_score))
    )

    return {
        "queue_depth": 0,  # placeholder until async queue is exposed
        "actions": {
            "total": total_actions or 0,
            "success": success_actions or 0,
            "failed": failed_actions or 0,
        },
        "confidence": {
            "average": float(avg_confidence) if avg_confidence else None,
        },
        "signals": {
            "expansion": None,
            "fatigue": None,
        },
    }


# -----------------------------------------------------
# CATEGORY INSIGHTS (UNCHANGED)
# -----------------------------------------------------
router.include_router(category_insights_router)

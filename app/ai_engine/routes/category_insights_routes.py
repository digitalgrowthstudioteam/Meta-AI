from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign

from app.ai_engine.models.ml_category_breakdown_stats import (
    MLCategoryBreakdownStat,
)
from app.ai_engine.models.ai_action_feedback import AIActionFeedback


router = APIRouter(
    prefix="/ai",
    tags=["AI Category & Feedback"],
)


# =====================================================
# CATEGORY INSIGHTS (READ-ONLY — GLOBAL SAFE)
# =====================================================
@router.get("/category-insights")
async def get_category_insights(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
    category: str = Query(...),
    window: str = Query("90d"),
):
    stmt = (
        select(MLCategoryBreakdownStat)
        .where(
            MLCategoryBreakdownStat.business_category == category,
            MLCategoryBreakdownStat.window_type == window,
        )
        .order_by(
            MLCategoryBreakdownStat.confidence_score.desc(),
            MLCategoryBreakdownStat.sample_size.desc(),
        )
    )

    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "category": category,
        "window": window,
        "insights": [
            {
                "age_range": r.age_range,
                "gender": r.gender,
                "city": r.city,
                "placement": r.placement,
                "device": r.device,
                "avg_roas": float(r.avg_roas) if r.avg_roas else None,
                "median_roas": float(r.median_roas) if r.median_roas else None,
                "avg_cpl": float(r.avg_cpl) if r.avg_cpl else None,
                "sample_size": r.sample_size,
                "confidence": float(r.confidence_score),
            }
            for r in rows
        ],
    }


# =====================================================
# AI ACTION FEEDBACK (STRICT USER + CAMPAIGN SCOPE)
# =====================================================
@router.post("/actions/feedback")
async def submit_ai_feedback(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
    campaign_id: str,
    rule_name: str,
    action_type: str,
    is_helpful: bool,
    confidence_at_time: float,
):
    # -------------------------------------------------
    # Validate campaign belongs to user
    # -------------------------------------------------
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.owner_user_id == user.id,
        )
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=404,
            detail="Campaign not found or access denied",
        )

    db.add(
        AIActionFeedback(
            user_id=user.id,
            campaign_id=campaign.id,
            rule_name=rule_name,
            action_type=action_type,
            is_helpful=is_helpful,
            confidence_at_time=confidence_at_time,
        )
    )

    await db.commit()
    return {"status": "ok"}

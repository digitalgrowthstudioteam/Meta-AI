from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.ai_engine.models.ml_category_breakdown_stats import (
    MLCategoryBreakdownStat,
)

router = APIRouter(
    prefix="/api/ai",
    tags=["AI Category Insights"],
)


@router.get("/category-insights")
async def get_category_insights(
    *,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_user),
    category: str = Query(..., description="Business category"),
    window: str = Query("90d", description="30d | 90d | lifetime"),
):
    """
    Global category-level performance insights.

    SAFE:
    - Aggregated
    - Anonymized
    - Read-only
    """

    stmt = (
        select(MLCategoryBreakdownStat)
        .where(
            MLCategoryBreakdownStat.business_category == category,
            MLCategoryBreakdownStat.window_type == window,
        )
        .order_by(
            MLCategoryBreakdownStat.avg_roas.desc().nullslast(),
            MLCategoryBreakdownStat.confidence_score.desc(),
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

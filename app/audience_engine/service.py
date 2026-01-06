from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.audience_engine.models import AudienceInsight
from app.campaigns.models import Campaign


class AudienceIntelligenceService:
    """
    Phase 20 — Audience Intelligence Engine

    🔒 RULES:
    - Suggest-only (NO auto apply)
    - Explainable outputs only
    - Deterministic + ML-ready
    """

    # =====================================================
    # CORE DECISION ENGINE
    # =====================================================
    @staticmethod
    async def generate_insight(
        *,
        db: AsyncSession,
        campaign: Campaign,
        fatigue_score: float,
        frequency: Optional[float],
        ctr_trend: Optional[float],
        cpm_trend: Optional[float],
        conversion_lift: Optional[float],
        audience_size_delta: Optional[int],
        similar_audience_source: Optional[str],
        source: str = "hybrid",
    ) -> AudienceInsight:
        """
        Produces KEEP / PAUSE / EXPAND decision.
        """

        # -------------------------
        # DECISION LOGIC (V1)
        # -------------------------
        if fatigue_score >= 0.75:
            suggestion = "PAUSE"
            reason = "High audience fatigue detected"
            confidence = 85

        elif conversion_lift and conversion_lift >= 0.15:
            suggestion = "EXPAND"
            reason = "Strong conversion lift potential"
            confidence = 80

        else:
            suggestion = "KEEP"
            reason = "Stable performance with acceptable fatigue"
            confidence = 65

        insight = AudienceInsight(
            campaign_id=campaign.id,
            suggestion_type=suggestion,
            reason=reason,
            confidence_score=confidence,
            fatigue_score=fatigue_score,
            frequency=frequency,
            ctr_trend=ctr_trend,
            cpm_trend=cpm_trend,
            conversion_lift=conversion_lift,
            audience_size_delta=audience_size_delta,
            similar_audience_source=similar_audience_source,
            source=source,
            created_at=datetime.utcnow(),
        )

        db.add(insight)
        await db.commit()
        await db.refresh(insight)
        return insight

    # =====================================================
    # READ INSIGHTS
    # =====================================================
    @staticmethod
    async def list_insights_for_campaign(
        *,
        db: AsyncSession,
        campaign_id,
        limit: int = 10,
    ):
        stmt = (
            select(AudienceInsight)
            .where(AudienceInsight.campaign_id == campaign_id)
            .order_by(AudienceInsight.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

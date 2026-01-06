from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.audience_engine.models import AudienceInsight
from app.campaigns.models import Campaign
from app.meta_insights.services.campaign_metrics_aggregation_service import (
    CampaignMetricsAggregationService,
)


class AudienceIntelligenceService:
    """
    Phase 20 — Audience Intelligence Engine

    🔒 RULES:
    - Suggest-only (NO auto apply)
    - Explainable outputs only
    - Deterministic, ML-ready
    """

    # =====================================================
    # END-TO-END INSIGHT GENERATION (PHASE 20 STEP 5)
    # =====================================================
    @staticmethod
    async def generate_insight_for_campaign(
        *,
        db: AsyncSession,
        campaign: Campaign,
        source: str = "hybrid",
    ) -> AudienceInsight:
        """
        Pulls Meta-derived signals → produces KEEP / PAUSE / EXPAND.
        """

        signal_service = CampaignMetricsAggregationService(db)

        signals = await signal_service.compute_audience_signals(
            campaign_id=str(campaign.id),
            short_window="7d",
            long_window="30d",
        )

        if not signals:
            raise ValueError("Insufficient data for audience insight")

        fatigue_score = signals.get("fatigue_score", 0.0)
        ctr_trend = signals.get("ctr_trend")
        conversion_lift = signals.get("conversion_lift")

        # -------------------------
        # DECISION LOGIC (V1)
        # -------------------------
        if fatigue_score >= 0.75:
            suggestion = "PAUSE"
            reason = "High audience fatigue detected from CTR decay"
            confidence = 85

        elif conversion_lift is not None and conversion_lift >= 0.15:
            suggestion = "EXPAND"
            reason = "Higher ROAS in recent window indicates expansion potential"
            confidence = 80

        else:
            suggestion = "KEEP"
            reason = "Performance stable with acceptable fatigue levels"
            confidence = 65

        insight = AudienceInsight(
            campaign_id=campaign.id,
            suggestion_type=suggestion,
            reason=reason,
            confidence_score=confidence,
            fatigue_score=fatigue_score,
            frequency=None,
            ctr_trend=ctr_trend,
            cpm_trend=None,
            conversion_lift=conversion_lift,
            audience_size_delta=None,
            similar_audience_source=None,
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
        from sqlalchemy import select

        stmt = (
            select(AudienceInsight)
            .where(AudienceInsight.campaign_id == campaign_id)
            .order_by(AudienceInsight.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

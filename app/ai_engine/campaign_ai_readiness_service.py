"""
Campaign AI Readiness Service

Purpose:
- Prepare AI-consumable intelligence
- Score campaigns and breakdowns
- Compare time windows
- Detect fatigue, scale, decay
- NO ML (rules + math only)
"""

from typing import Dict, List, Literal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


WindowType = Literal["1d", "3d", "7d", "14d", "30d", "90d", "lifetime"]


class CampaignAIReadinessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CAMPAIGN-LEVEL AI SCORE
    # =========================================================
    async def get_campaign_ai_score(
        self,
        campaign_id: str,
        short_window: WindowType = "7d",
        long_window: WindowType = "30d",
    ) -> Dict:
        short = await self._get_campaign_window(campaign_id, short_window)
        long = await self._get_campaign_window(campaign_id, long_window)

        if not short or not long:
            return {"status": "insufficient_data"}

        score = self._score_performance(short, long)

        return {
            "campaign_id": campaign_id,
            "short_window": short_window,
            "long_window": long_window,
            "ai_score": score,
            "signals": self._detect_signals(short, long),
        }

    # =========================================================
    # BREAKDOWN RANKING (WHAT WORKS BEST)
    # =========================================================
    async def rank_breakdowns(
        self,
        campaign_id: str,
        window: WindowType,
        dimension: Literal[
            "creative_id",
            "placement",
            "city",
            "gender",
            "age_range",
            "device",
        ],
        limit: int = 5,
    ) -> List[Dict]:
        result = await self.db.execute(
            text(
                f"""
                SELECT
                    {dimension} AS key,
                    impressions,
                    clicks,
                    spend,
                    conversions,
                    revenue,
                    ctr,
                    cpl,
                    cpa,
                    roas
                FROM campaign_breakdown_aggregates
                WHERE campaign_id = :campaign_id
                  AND window_type = :window
                  AND {dimension} IS NOT NULL
                ORDER BY
                    roas DESC NULLS LAST,
                    ctr DESC NULLS LAST,
                    conversions DESC
                LIMIT :limit
                """
            ),
            {
                "campaign_id": campaign_id,
                "window": window,
                "limit": limit,
            },
        )

        return [dict(row._mapping) for row in result.fetchall()]

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================
    async def _get_campaign_window(self, campaign_id: str, window: str) -> Dict | None:
        result = await self.db.execute(
            text(
                """
                SELECT *
                FROM campaign_metrics_aggregates
                WHERE campaign_id = :campaign_id
                  AND window_type = :window
                  AND is_complete_window = true
                """
            ),
            {"campaign_id": campaign_id, "window": window},
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def _score_performance(self, short: Dict, long: Dict) -> float:
        """
        Simple normalized score (0–100)
        """
        score = 0.0

        if short.get("roas") and long.get("roas"):
            score += min((short["roas"] / long["roas"]) * 40, 40)

        if short.get("ctr") and long.get("ctr"):
            score += min((short["ctr"] / long["ctr"]) * 30, 30)

        if short.get("conversions") and long.get("conversions"):
            score += min(
                (short["conversions"] / long["conversions"]) * 30, 30
            )

        return round(score, 2)

    def _detect_signals(self, short: Dict, long: Dict) -> Dict:
        signals = {}

        if short["ctr"] and long["ctr"]:
            if short["ctr"] < long["ctr"] * 0.8:
                signals["fatigue"] = True
            elif short["ctr"] > long["ctr"] * 1.2:
                signals["scale"] = True

        if short["roas"] and long["roas"]:
            if short["roas"] < long["roas"] * 0.75:
                signals["decay"] = True

        return signals

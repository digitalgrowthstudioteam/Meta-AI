"""
Meta Campaign Insights Client

Purpose:
- Fetch daily campaign insights from Meta
- Support breakdown-level performance for AI/ML
- Isolated client (NO DB writes)
"""

from datetime import date
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign


class MetaCampaignInsightsClient:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_daily_insights(
        self,
        campaign: Campaign,
        target_date: date,
    ) -> Optional[Dict[str, Any]]:
        """
        CONTRACT (LOCKED):

        Must return:
        {
            "campaign": { campaign-level metrics },
            "breakdowns": [
                {
                    "creative_id": str | None,
                    "placement": str | None,
                    "city": str | None,
                    "gender": str | None,
                    "age_range": str | None,
                    "device": str | None,
                    "impressions": int,
                    "clicks": int,
                    "spend": float,
                    "conversions": int,
                    "revenue": float | None
                }
            ]
        }

        TEMP STUB — real Meta Graph API wiring will replace this.
        """

        # -----------------------------
        # CAMPAIGN-LEVEL METRICS
        # -----------------------------
        campaign_metrics = {
            "impressions": 0,
            "clicks": 0,
            "spend": 0.0,
            "conversions": 0,
            "revenue": 0.0,
        }

        # -----------------------------
        # BREAKDOWN-LEVEL METRICS
        # -----------------------------
        breakdowns: List[Dict[str, Any]] = []

        # Example placeholder (safe no-op)
        # Real Meta API will populate these rows
        # Keeping structure locked for AI + aggregation layers
        breakdowns.append(
            {
                "creative_id": None,
                "placement": None,
                "city": None,
                "gender": None,
                "age_range": None,
                "device": None,
                "impressions": 0,
                "clicks": 0,
                "spend": 0.0,
                "conversions": 0,
                "revenue": 0.0,
            }
        )

        return {
            "campaign": campaign_metrics,
            "breakdowns": breakdowns,
        }

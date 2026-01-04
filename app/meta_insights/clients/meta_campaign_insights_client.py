"""
Meta Campaign Insights Client

Purpose:
- Fetch daily campaign insights from Meta
- READ-ONLY
- NO DB writes
- Phase 6.5 compatible (campaign-level metrics only)
"""

from datetime import date
from typing import Dict, Any, Optional

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
        PHASE 6.5 CONTRACT (LOCKED)

        Must return FLAT campaign-level metrics:
        {
            "impressions": int,
            "clicks": int,
            "spend": float,
            "leads": int,
            "purchases": int,
            "purchase_value": float
        }

        TEMP STUB — real Meta Graph API will replace this.
        """

        # -----------------------------
        # SAFE NO-OP PLACEHOLDER
        # -----------------------------
        # Ensures ingestion pipeline works end-to-end
        # AI will remain empty until real data arrives

        return {
            "impressions": 0,
            "clicks": 0,
            "spend": 0.0,
            "leads": 0,
            "purchases": 0,
            "purchase_value": 0.0,
        }

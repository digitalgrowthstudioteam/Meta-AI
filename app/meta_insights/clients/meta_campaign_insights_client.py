"""
Meta Campaign Insights Client

Purpose:
- Fetch daily campaign insights from Meta
- Fetch breakdown-level insights (Phase 8)
- READ-ONLY
- NEVER raise
- Stub-safe for now
"""

from datetime import date, datetime
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount


class MetaCampaignInsightsClient:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================
    # CAMPAIGN-LEVEL (PHASE 6.5)
    # =====================================================
    async def fetch_daily_insights(
        self,
        campaign: Campaign,
        target_date: date,
    ) -> Dict[str, Any]:
        """
        PHASE 6.5 CONTRACT (LOCKED)

        Always returns a dict.
        All-zero payload = NO DATA.
        """

        return {
            "impressions": 0,
            "clicks": 0,
            "spend": 0.0,
            "leads": 0,
            "purchases": 0,
            "purchase_value": 0.0,
        }

    # =====================================================
    # BREAKDOWN-LEVEL (PHASE 8)
    # =====================================================
    async def fetch_daily_insights_with_breakdown(
        self,
        *,
        ad_account: MetaAdAccount,
        since: date,
        until: date,
        breakdowns: List[str],
    ) -> List[Dict[str, Any]]:
        """
        PHASE 8 CONTRACT (LOCKED)

        Returns list of rows with keys:
        - campaign_meta_id
        - metric_date
        - breakdown dimensions (optional)
        - impressions, clicks, spend, conversions, conversion_value
        - ctr, cpl, cpa, roas
        - meta_fetched_at

        STUB MODE:
        - Returns empty list
        - Never raises
        """

        # -----------------------------
        # SAFE STUB — NO META CALL
        # -----------------------------
        return []

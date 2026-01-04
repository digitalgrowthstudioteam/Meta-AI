"""
Meta Campaign Insights Client

Purpose:
- Fetch daily campaign-level insights from Meta
- Isolated client (no DB writes)
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
        TEMP stub.
        Replace with real Meta Graph API integration.
        Must return a dict matching expected metrics or None.
        """
        return None

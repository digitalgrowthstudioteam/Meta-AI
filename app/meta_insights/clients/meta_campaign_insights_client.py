from datetime import date
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from app.campaigns.models import Campaign


class MetaCampaignInsightsClient:
    """
    Temporary safe client stub.
    Real Meta API logic will be added later.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_daily_insights(
        self,
        campaign: Campaign,
        target_date: date,
    ) -> Dict[str, Any]:
        # SAFE placeholder to unblock system
        return {
            "impressions": 0,
            "clicks": 0,
            "spend": 0,
            "leads": 0,
            "purchases": 0,
            "purchase_value": 0,
        }

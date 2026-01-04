"""
Meta Campaign Insights Client

Purpose:
- Fetch daily campaign insights from Meta
- READ-ONLY
- NEVER raise (Phase 6.5 requirement)
- Always return a safe dict so ingestion can SKIP cleanly
"""

from datetime import date
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign


class MetaCampaignInsightsClient:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def fetch_daily_insights(
        self,
        campaign: Campaign,
        target_date: date,
    ) -> Dict[str, Any]:
        """
        PHASE 6.5 CONTRACT (LOCKED)

        MUST:
        - Never raise
        - Always return a dict
        - All-zero payload means: NO DATA (stub / skipped)
        """

        try:
            # -----------------------------
            # TEMP SAFE STUB (NO META CALL)
            # -----------------------------
            return {
                "impressions": 0,
                "clicks": 0,
                "spend": 0.0,
                "leads": 0,
                "purchases": 0,
                "purchase_value": 0.0,
            }

        except Exception:
            # Absolute safety net — NEVER FAIL PIPELINE
            return {
                "impressions": 0,
                "clicks": 0,
                "spend": 0.0,
                "leads": 0,
                "purchases": 0,
                "purchase_value": 0.0,
            }

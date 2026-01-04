from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.campaigns.models import Campaign
from app.meta_insights.models.campaign_daily_metrics import CampaignDailyMetrics


class CategoryInferenceService:
    """
    Infers business category for a campaign using explainable heuristics.

    NO DB writes.
    NO ML training.
    Deterministic, auditable, ML-ready.
    """

    # ---------------------------------------
    # CATEGORY KEYWORD MAP (INITIAL SEED)
    # ---------------------------------------
    KEYWORD_CATEGORY_MAP = {
        "skin": "Skin Care",
        "skincare": "Skin Care",
        "derma": "Skin Care",
        "acne": "Skin Care",
        "beauty": "Beauty",
        "hair": "Hair Care",
        "salon": "Beauty",
        "loan": "Finance",
        "credit": "Finance",
        "emi": "Finance",
        "insurance": "Insurance",
        "policy": "Insurance",
        "real estate": "Real Estate",
        "property": "Real Estate",
        "flat": "Real Estate",
        "home": "Real Estate",
        "education": "Education",
        "course": "Education",
        "training": "Education",
        "fitness": "Fitness",
        "gym": "Fitness",
        "yoga": "Fitness",
        "hospital": "Healthcare",
        "clinic": "Healthcare",
        "doctor": "Healthcare",
        "dentist": "Healthcare",
    }

    async def infer_category(
        self,
        *,
        db: AsyncSession,
        campaign_id: str,
    ) -> Dict:
        """
        Infer category for a campaign.

        Returns:
        {
            inferred_category: str | None,
            confidence_score: float,
            signals: List[str]
        }
        """

        # ---------------------------------------
        # LOAD CAMPAIGN
        # ---------------------------------------
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            return {
                "inferred_category": None,
                "confidence_score": 0.0,
                "signals": [],
            }

        signals: List[str] = []
        scores: Dict[str, float] = {}

        # ---------------------------------------
        # SIGNAL 1 — CAMPAIGN NAME KEYWORDS
        # ---------------------------------------
        name = campaign.name.lower()

        for keyword, category in self.KEYWORD_CATEGORY_MAP.items():
            if keyword in name:
                scores[category] = scores.get(category, 0) + 0.4
                signals.append(f"name_keyword:{keyword}")

        # ---------------------------------------
        # SIGNAL 2 — OBJECTIVE TYPE
        # ---------------------------------------
        if campaign.objective.upper() in ("LEAD", "LEAD_GENERATION"):
            scores["Services"] = scores.get("Services", 0) + 0.1
            signals.append("objective:lead")

        if campaign.objective.upper() in ("SALES", "CONVERSIONS"):
            scores["Ecommerce"] = scores.get("Ecommerce", 0) + 0.1
            signals.append("objective:sales")

        # ---------------------------------------
        # SIGNAL 3 — PERFORMANCE SHAPE (BASIC)
        # ---------------------------------------
        result = await db.execute(
            select(
                func.avg(CampaignDailyMetrics.cpl),
                func.avg(CampaignDailyMetrics.roas),
            ).where(
                CampaignDailyMetrics.campaign_id == campaign.id
            )
        )
        avg_cpl, avg_roas = result.first() or (None, None)

        if avg_roas and avg_roas > 3:
            scores["Ecommerce"] = scores.get("Ecommerce", 0) + 0.15
            signals.append("high_roas")

        if avg_cpl and avg_cpl < 150:
            scores["Lead Gen"] = scores.get("Lead Gen", 0) + 0.1
            signals.append("low_cpl")

        # ---------------------------------------
        # FINAL RESOLUTION
        # ---------------------------------------
        if not scores:
            return {
                "inferred_category": None,
                "confidence_score": 0.0,
                "signals": signals,
            }

        inferred_category = max(scores, key=scores.get)
        confidence_score = min(1.0, scores[inferred_category])

        return {
            "inferred_category": inferred_category,
            "confidence_score": round(confidence_score, 2),
            "signals": signals,
        }

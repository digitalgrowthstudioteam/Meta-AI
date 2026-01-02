from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign
from app.ai_engine.models.action_models import AIAction
from app.ai_engine.aggregation_engine.campaign_aggregation_service import (
    CampaignAggregationService,
)


class CampaignDecisionService:
    """
    Campaign-level AI Decision Engine (Phase 8A).

    Responsibilities:
    - Consume MATERIALIZED aggregated metrics
    - Apply objective-aware RULES
    - Apply HEURISTIC confidence scoring
    - Produce AIAction records (SUGGESTED only)
    - Generate explainability payloads

    Guarantees:
    - NO auto-apply
    - NO Meta mutation
    - NO UI coupling
    """

    # -------------------------------
    # Heuristic thresholds (tunable)
    # -------------------------------
    LEAD_RULES = {
        "ctr_min": 0.8,          # %
        "cpl_increase_pct": 25,  # %
    }

    SALES_RULES = {
        "roas_min": 1.2,
        "cpa_increase_pct": 25,  # %
    }

    # -------------------------------
    # Confidence heuristics
    # -------------------------------
    MIN_IMPRESSIONS = {
        "LOW": 500,
        "MEDIUM": 2000,
        "HIGH": 5000,
    }

    @staticmethod
    async def decide_for_campaign(
        *,
        db: AsyncSession,
        campaign: Campaign,
        as_of_date: date,
    ) -> Optional[AIAction]:
        """
        Generates a SINGLE AIAction suggestion for a campaign,
        or returns None if no action is warranted.
        """

        # Guard rails
        if not campaign.ai_active or campaign.is_archived or campaign.admin_locked:
            return None

        aggregates = await CampaignAggregationService.aggregate_for_campaign(
            db=db,
            campaign=campaign,
            as_of_date=as_of_date,
        )

        # We use short vs stable windows for heuristics
        short = aggregates.get("3D")
        stable = aggregates.get("14D")

        if not short or not stable:
            return None

        objective = campaign.objective.upper()

        if objective == "LEAD":
            return CampaignDecisionService._lead_decision(
                campaign=campaign,
                short=short,
                stable=stable,
                as_of_date=as_of_date,
            )

        if objective == "SALES":
            return CampaignDecisionService._sales_decision(
                campaign=campaign,
                short=short,
                stable=stable,
                as_of_date=as_of_date,
            )

        return None

    # =====================================================
    # LEAD CAMPAIGN LOGIC
    # =====================================================
    @staticmethod
    def _lead_decision(
        *,
        campaign: Campaign,
        short: Dict,
        stable: Dict,
        as_of_date: date,
    ) -> Optional[AIAction]:

        rules = CampaignDecisionService.LEAD_RULES

        # Metrics
        short_ctr = short.get("ctr")
        short_cpl = short.get("cpl")
        stable_cpl = stable.get("cpl")

        if short_cpl and stable_cpl:
            cpl_change_pct = ((short_cpl - stable_cpl) / stable_cpl) * 100
        else:
            cpl_change_pct = 0

        # Rule: performance deterioration
        if (
            short_ctr is not None
            and short_ctr < rules["ctr_min"]
            and cpl_change_pct > rules["cpl_increase_pct"]
        ):
            confidence = CampaignDecisionService._confidence_from_impressions(
                impressions=short.get("impressions", 0)
            )

            return AIAction(
                campaign_id=campaign.id,
                action_type="PAUSE_CAMPAIGN",
                objective_type="LEAD",
                time_window="3D",
                before_state={"status": campaign.status},
                after_state={"status": "PAUSED"},
                explainability={
                    "metrics": {
                        "3D": short,
                        "14D": stable,
                    },
                    "analysis": {
                        "ctr_drop": short_ctr,
                        "cpl_change_pct": round(cpl_change_pct, 2),
                    },
                    "reason": (
                        "CTR dropped below threshold and CPL increased significantly "
                        "over the last 3 days compared to 14-day baseline."
                    ),
                },
                confidence_level=confidence,
                status="SUGGESTED",
                executed_mode="SUGGEST",
            )

        return None

    # =====================================================
    # SALES CAMPAIGN LOGIC
    # =====================================================
    @staticmethod
    def _sales_decision(
        *,
        campaign: Campaign,
        short: Dict,
        stable: Dict,
        as_of_date: date,
    ) -> Optional[AIAction]:

        rules = CampaignDecisionService.SALES_RULES

        short_roas = short.get("roas")
        short_cpa = short.get("cpa")
        stable_cpa = stable.get("cpa")

        if short_cpa and stable_cpa:
            cpa_change_pct = ((short_cpa - stable_cpa) / stable_cpa) * 100
        else:
            cpa_change_pct = 0

        if (
            short_roas is not None
            and short_roas < rules["roas_min"]
            and cpa_change_pct > rules["cpa_increase_pct"]
        ):
            confidence = CampaignDecisionService._confidence_from_impressions(
                impressions=short.get("impressions", 0)
            )

            return AIAction(
                campaign_id=campaign.id,
                action_type="BUDGET_DECREASE",
                objective_type="SALES",
                time_window="3D",
                before_state={"budget": "current"},
                after_state={"budget": "decrease_suggested"},
                explainability={
                    "metrics": {
                        "3D": short,
                        "14D": stable,
                    },
                    "analysis": {
                        "roas": short_roas,
                        "cpa_change_pct": round(cpa_change_pct, 2),
                    },
                    "reason": (
                        "ROAS dropped below threshold and CPA increased "
                        "compared to 14-day baseline."
                    ),
                },
                confidence_level=confidence,
                status="SUGGESTED",
                executed_mode="SUGGEST",
            )

        return None

    # =====================================================
    # CONFIDENCE HEURISTIC
    # =====================================================
    @staticmethod
    def _confidence_from_impressions(impressions: int) -> str:
        """
        Simple, explainable confidence heuristic.
        """

        if impressions >= CampaignDecisionService.MIN_IMPRESSIONS["HIGH"]:
            return "HIGH"
        if impressions >= CampaignDecisionService.MIN_IMPRESSIONS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

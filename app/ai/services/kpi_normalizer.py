from typing import Dict, Optional


LEAD_OBJECTIVES = {
    "LEAD_GENERATION",
    "LEAD",
    "OUTCOME_LEADS",
    "ENGAGEMENT",
    "MESSAGES",
    "LINK_CLICKS",
    "TRAFFIC",
}

SALES_OBJECTIVES = {
    "CONVERSIONS",
    "SALES",
    "OUTCOME_SALES",
    "PURCHASE",
}


class KPINormalizer:
    """
    Phase 7.1 — KPI Normalization

    Converts raw Meta insights into
    comparable KPIs per campaign.

    Rules:
    - Read-only
    - Campaign-level
    - No aggregation
    """

    @staticmethod
    def _extract_action_count(actions: list, action_type: str) -> int:
        for a in actions or []:
            if a.get("action_type") == action_type:
                return int(float(a.get("value", 0)))
        return 0

    @staticmethod
    def _extract_action_value(values: list, action_type: str) -> float:
        for v in values or []:
            if v.get("action_type") == action_type:
                return float(v.get("value", 0.0))
        return 0.0

    @classmethod
    def normalize(
        cls,
        *,
        objective: str,
        insights: Dict,
    ) -> Dict:
        """
        Normalize KPIs for ONE campaign.

        Returns:
            {
              "mode": "LEAD" | "SALES",
              "spend": float,
              "primary_count": int,
              "primary_cost": float | None,
              "secondary_rate": float | None,
              "roas": float | None
            }
        """

        spend = float(insights.get("spend", 0))
        clicks = int(insights.get("clicks", 0))
        actions = insights.get("actions", [])
        values = insights.get("action_values", [])

        purchases = cls._extract_action_count(actions, "purchase")
        revenue = cls._extract_action_value(values, "purchase")
        leads = (
            cls._extract_action_count(actions, "lead")
            or cls._extract_action_count(actions, "onsite_conversion.messaging_conversation_started_7d")
            or clicks
        )

        objective = (objective or "").upper()

        # ---------------------------
        # SALES MODE (strict)
        # ---------------------------
        if objective in SALES_OBJECTIVES and purchases > 0:
            cpa = spend / purchases if purchases > 0 else None
            roas = revenue / spend if spend > 0 else None

            return {
                "mode": "SALES",
                "spend": spend,
                "primary_count": purchases,
                "primary_cost": cpa,
                "secondary_rate": None,
                "roas": roas,
            }

        # ---------------------------
        # LEAD MODE (default & safe)
        # ---------------------------
        cpl = spend / leads if leads > 0 else None
        lead_rate = leads / clicks if clicks > 0 else None

        return {
            "mode": "LEAD",
            "spend": spend,
            "primary_count": leads,
            "primary_cost": cpl,
            "secondary_rate": lead_rate,
            "roas": None,
        }

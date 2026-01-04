import httpx
from typing import List, Dict, Optional
from datetime import date, datetime

from app.meta_api.models import MetaAdAccount


class MetaCampaignInsightsClient:
    """
    READ-ONLY Meta Campaign Insights Client.

    Responsibilities:
    - Fetch DAILY performance insights per campaign
    - Fetch DAILY performance insights with breakdowns
    - Respect Meta Ad Account timezone
    - Normalize Meta insights payload
    - Never mutate Meta
    - Never apply business logic
    """

    GRAPH_BASE_URL = "https://graph.facebook.com/v19.0"

    # =====================================================
    # BASE — CAMPAIGN LEVEL (UNCHANGED)
    # =====================================================
    @classmethod
    async def fetch_daily_insights(
        cls,
        *,
        ad_account: MetaAdAccount,
        since: date,
        until: date,
    ) -> List[Dict]:
        """
        Fetch DAILY insights for all campaigns in an ad account.
        """

        if not ad_account.access_token:
            raise RuntimeError("Meta ad account missing access token")

        url = f"{cls.GRAPH_BASE_URL}/act_{ad_account.meta_account_id}/insights"

        params = {
            "level": "campaign",
            "time_increment": 1,
            "time_range": {
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
            "fields": ",".join(
                [
                    "campaign_id",
                    "impressions",
                    "clicks",
                    "spend",
                    "actions",
                    "action_values",
                    "ctr",
                    "cpc",
                    "cost_per_action_type",
                    "purchase_roas",
                    "date_start",
                ]
            ),
            "access_token": ad_account.access_token,
        }

        return await cls._execute_and_normalize(url, params)

    # =====================================================
    # BREAKDOWN — DAILY INSIGHTS (NEW)
    # =====================================================
    @classmethod
    async def fetch_daily_insights_with_breakdown(
        cls,
        *,
        ad_account: MetaAdAccount,
        since: date,
        until: date,
        breakdowns: List[str],
    ) -> List[Dict]:
        """
        Fetch DAILY insights with a specific breakdown.

        Example breakdowns:
        - ["ad_id"]
        - ["platform", "placement"]
        - ["age", "gender"]
        - ["region"]
        """

        if not ad_account.access_token:
            raise RuntimeError("Meta ad account missing access token")

        url = f"{cls.GRAPH_BASE_URL}/act_{ad_account.meta_account_id}/insights"

        params = {
            "level": "campaign",
            "time_increment": 1,
            "breakdowns": ",".join(breakdowns),
            "time_range": {
                "since": since.isoformat(),
                "until": until.isoformat(),
            },
            "fields": ",".join(
                [
                    "campaign_id",
                    "ad_id",
                    "impressions",
                    "clicks",
                    "spend",
                    "actions",
                    "action_values",
                    "ctr",
                    "cpc",
                    "cost_per_action_type",
                    "purchase_roas",
                    "date_start",
                ]
            ),
            "access_token": ad_account.access_token,
        }

        return await cls._execute_and_normalize(
            url,
            params,
            breakdowns=breakdowns,
        )

    # =====================================================
    # INTERNAL — EXECUTION & NORMALIZATION
    # =====================================================
    @classmethod
    async def _execute_and_normalize(
        cls,
        url: str,
        params: Dict,
        breakdowns: Optional[List[str]] = None,
    ) -> List[Dict]:
        insights: List[Dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Meta Insights API error {response.status_code}: {response.text}"
                    )

                payload = response.json()

                for item in payload.get("data", []):
                    insights.append(
                        cls._normalize_row(
                            item=item,
                            breakdowns=breakdowns,
                        )
                    )

                paging = payload.get("paging", {})
                next_url = paging.get("next")

                if not next_url:
                    break

                url = next_url
                params = None

        return insights

    # =====================================================
    # NORMALIZATION (NO BUSINESS LOGIC)
    # =====================================================
    @staticmethod
    def _normalize_row(
        *,
        item: Dict,
        breakdowns: Optional[List[str]] = None,
    ) -> Dict:
        impressions = int(item.get("impressions", 0))
        clicks = int(item.get("clicks", 0))
        spend = float(item.get("spend", 0.0))

        conversions = 0
        for action in item.get("actions", []):
            if action.get("action_type") in ("lead", "purchase"):
                conversions += int(action.get("value", 0))

        conversion_value = None
        roas = None

        purchase_roas = item.get("purchase_roas")
        if purchase_roas and isinstance(purchase_roas, list):
            roas = float(purchase_roas[0].get("value", 0))
            for av in item.get("action_values", []):
                if av.get("action_type") == "purchase":
                    conversion_value = float(av.get("value", 0))

        ctr = float(item.get("ctr")) if item.get("ctr") else None

        cpl = None
        cpa = None
        for cpa_item in item.get("cost_per_action_type", []):
            if cpa_item.get("action_type") == "lead":
                cpl = float(cpa_item.get("value"))
            if cpa_item.get("action_type") == "purchase":
                cpa = float(cpa_item.get("value"))

        row = {
            "campaign_meta_id": item.get("campaign_id"),
            "metric_date": date.fromisoformat(item.get("date_start")),
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "conversions": conversions,
            "conversion_value": conversion_value,
            "ctr": ctr,
            "cpl": cpl,
            "cpa": cpa,
            "roas": roas,
            "meta_fetched_at": datetime.utcnow(),
        }

        # Attach breakdown fields dynamically
        if breakdowns:
            for b in breakdowns:
                row[b] = item.get(b)

        return row

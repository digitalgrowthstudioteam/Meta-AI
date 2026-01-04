from typing import Dict, List, Optional
from datetime import date

import httpx

from app.meta_api.models import MetaAdAccount
from app.meta_api.meta_client import MetaAPIError


class MetaInsightsClient:
    """
    Read-only Meta Insights client.

    Rules:
    - NO database writes
    - NO business logic
    - NO aggregation
    - Fetch raw campaign performance only
    """

    GRAPH_BASE = "https://graph.facebook.com/v19.0"

    # -----------------------------------------------------
    # FETCH CAMPAIGN INSIGHTS
    # -----------------------------------------------------
    @classmethod
    async def fetch_campaign_insights(
        cls,
        *,
        ad_account: MetaAdAccount,
        since: Optional[date] = None,
        until: Optional[date] = None,
    ) -> List[Dict]:
        """
        Fetch raw campaign-level insights for a given ad account.

        Time window:
        - If since/until provided → bounded window
        - If not provided → lifetime
        """

        if not hasattr(ad_account, "access_token") or not ad_account.access_token:
            raise MetaAPIError("Missing Meta access token")

        url = f"{cls.GRAPH_BASE}/{ad_account.meta_account_id}/insights"

        params = {
            "level": "campaign",
            "fields": ",".join(
                [
                    "campaign_id",
                    "spend",
                    "impressions",
                    "clicks",
                    "ctr",
                    "cpc",
                    "actions",
                    "action_values",
                ]
            ),
            "access_token": ad_account.access_token,
        }

        if since and until:
            params["time_range"] = {
                "since": since.isoformat(),
                "until": until.isoformat(),
            }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)

        if resp.status_code != 200:
            raise MetaAPIError(resp.text)

        data = resp.json()
        return data.get("data", [])

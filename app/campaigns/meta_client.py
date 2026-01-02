import httpx
from typing import List, Dict

from app.core.config import settings
from app.meta.models import MetaAdAccount


class MetaCampaignClient:
    """
    READ-ONLY Meta Campaign Client.

    Responsibilities:
    - Fetch campaigns from Meta
    - Handle pagination
    - Normalize payload
    - Never mutate Meta
    """

    GRAPH_BASE_URL = "https://graph.facebook.com/v19.0"

    @classmethod
    async def fetch_campaigns(
        cls,
        *,
        ad_account: MetaAdAccount,
    ) -> List[Dict]:
        """
        Fetch ALL campaigns for a Meta Ad Account.

        Returns normalized campaign dicts:
        {
            "id": str,
            "name": str,
            "objective": str,
            "status": str
        }
        """

        if not ad_account.access_token:
            raise RuntimeError("Meta ad account missing access token")

        url = f"{cls.GRAPH_BASE_URL}/act_{ad_account.meta_account_id}/campaigns"

        params = {
            "fields": "id,name,objective,status",
            "limit": 50,
            "access_token": ad_account.access_token,
        }

        campaigns: List[Dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    raise RuntimeError(
                        f"Meta API error {response.status_code}: {response.text}"
                    )

                payload = response.json()

                for item in payload.get("data", []):
                    campaigns.append(
                        {
                            "id": item["id"],
                            "name": item.get("name", ""),
                            "objective": item.get("objective", "UNKNOWN"),
                            "status": item.get("status", "UNKNOWN"),
                        }
                    )

                paging = payload.get("paging", {})
                next_url = paging.get("next")

                if not next_url:
                    break

                # Meta returns a full URL for next page
                url = next_url
                params = None  # next already contains params

        return campaigns

import httpx
from typing import List, Dict

from app.meta_api.models import MetaAdAccount, MetaOAuthToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


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
        db: AsyncSession,
        user_id,
        ad_account: MetaAdAccount,
    ) -> List[Dict]:
        """
        Fetch ALL campaigns for a Meta Ad Account.
        """

        # -------------------------------------------------
        # Resolve active Meta OAuth token for user
        # -------------------------------------------------
        result = await db.execute(
            select(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
            .limit(1)
        )
        token = result.scalar_one_or_none()

        if not token:
            raise RuntimeError("No active Meta OAuth token found")

        url = f"{cls.GRAPH_BASE_URL}/{ad_account.meta_account_id}/campaigns"

        params = {
            "fields": "id,name,objective,effective_status",
            "limit": 50,
            "access_token": token.access_token,
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
                    status = item.get("effective_status", "UNKNOWN")

                    if status in {"DELETED", "ARCHIVED"}:
                        continue

                    campaigns.append(
                        {
                            "id": item["id"],
                            "name": item.get("name", ""),
                            "objective": item.get("objective", "UNKNOWN"),
                            "status": status,
                        }
                    )

                paging = payload.get("paging", {})
                next_url = paging.get("next")

                if not next_url:
                    break

                url = next_url
                params = None

        return campaigns

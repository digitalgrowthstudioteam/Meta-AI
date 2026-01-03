from typing import List, Dict, Optional
import httpx
from datetime import datetime

from app.meta_api.models import MetaAdAccount
from app.meta_api.models import MetaOAuthToken


class MetaAPIError(Exception):
    pass


class MetaCampaignClient:
    """
    Low-level Meta Graph API client.
    - NO database writes
    - NO business logic
    - NO enforcement
    """

    GRAPH_BASE = "https://graph.facebook.com/v19.0"

    # =====================================================
    # INTERNAL: GET ACTIVE USER TOKEN
    # =====================================================
    @staticmethod
    async def _get_active_token(db, user_id: str) -> str:
        token = (
            await db.execute(
                MetaOAuthToken.__table__
                .select()
                .where(
                    MetaOAuthToken.user_id == user_id,
                    MetaOAuthToken.is_active.is_(True),
                )
            )
        ).first()

        if not token:
            raise MetaAPIError("Meta account not connected")

        return token.access_token

    # =====================================================
    # FETCH AD ACCOUNTS
    # =====================================================
    @classmethod
    async def fetch_ad_accounts(
        cls,
        *,
        db,
        user_id: str,
    ) -> List[Dict]:
        access_token = await cls._get_active_token(db, user_id)

        url = f"{cls.GRAPH_BASE}/me/adaccounts"
        params = {
            "fields": "id,name,account_status",
            "access_token": access_token,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)

        if resp.status_code != 200:
            raise MetaAPIError(resp.text)

        data = resp.json()
        return data.get("data", [])

    # =====================================================
    # FETCH CAMPAIGNS (PER AD ACCOUNT)
    # =====================================================
    @classmethod
    async def fetch_campaigns(
        cls,
        *,
        ad_account: MetaAdAccount,
    ) -> List[Dict]:
        """
        ad_account.meta_account_id must be like: act_123456789
        """

        url = f"{cls.GRAPH_BASE}/{ad_account.meta_account_id}/campaigns"
        params = {
            "fields": "id,name,status,objective",
            "access_token": ad_account.access_token
            if hasattr(ad_account, "access_token")
            else None,
        }

        if not params["access_token"]:
            raise MetaAPIError("Missing Meta access token")

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)

        if resp.status_code != 200:
            raise MetaAPIError(resp.text)

        data = resp.json()
        return data.get("data", [])

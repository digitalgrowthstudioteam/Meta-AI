from datetime import datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_api.models import (
    MetaOAuthToken,
    MetaAdAccount,
    UserMetaAdAccount,
)
from app.campaigns.models import Campaign
from app.core.config import settings


META_GRAPH_BASE = "https://graph.facebook.com/v19.0"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


class MetaOAuthService:
    """
    Handles Meta OAuth token exchange & storage.
    """

    @staticmethod
    async def _exchange_for_long_lived_token(short_token: str) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                META_TOKEN_URL,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": short_token,
                },
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def store_token(
        db: AsyncSession,
        *,
        user_id: UUID,
        code: str,
    ) -> MetaOAuthToken:
        from app.meta_api.oauth import exchange_code_for_token

        short_token_data = await exchange_code_for_token(code)
        short_token = short_token_data["access_token"]

        long_token_data = await MetaOAuthService._exchange_for_long_lived_token(
            short_token
        )

        expires_in = long_token_data.get("expires_in")
        expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in)
            if expires_in
            else None
        )

        await db.execute(
            update(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
            .values(is_active=False)
        )

        token = MetaOAuthToken(
            user_id=user_id,
            access_token=long_token_data["access_token"],
            token_type=long_token_data.get("token_type"),
            expires_at=expires_at,
            is_active=True,
        )

        db.add(token)
        await db.commit()
        await db.refresh(token)

        return token


class MetaAdAccountService:
    """
    Read-only sync of Meta Ad Accounts.
    """

    @staticmethod
    async def sync_user_ad_accounts(
        *,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        result = await db.execute(
            select(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
        )
        token = result.scalar_one_or_none()

        if not token:
            raise RuntimeError("Meta account not connected")

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{META_GRAPH_BASE}/me/adaccounts",
                params={
                    "access_token": token.access_token,
                    "fields": "id,name,account_status",
                },
            )
            response.raise_for_status()
            data = response.json()

        processed = 0

        for acct in data.get("data", []):
            meta_account_id = acct["id"]
            account_name = acct.get("name", "")

            result = await db.execute(
                select(MetaAdAccount).where(
                    MetaAdAccount.meta_account_id == meta_account_id
                )
            )
            meta_account = result.scalar_one_or_none()

            if not meta_account:
                meta_account = MetaAdAccount(
                    meta_account_id=meta_account_id,
                    account_name=account_name,
                    is_active=True,
                )
                db.add(meta_account)
                await db.flush()

            result = await db.execute(
                select(UserMetaAdAccount).where(
                    UserMetaAdAccount.user_id == user_id,
                    UserMetaAdAccount.meta_ad_account_id == meta_account.id,
                )
            )
            if not result.scalar_one_or_none():
                db.add(
                    UserMetaAdAccount(
                        user_id=user_id,
                        meta_ad_account_id=meta_account.id,
                        role="owner",
                    )
                )

            processed += 1

        await db.commit()
        return processed


class MetaCampaignService:
    """
    Manual, read-only Meta Campaign sync.
    """

    @staticmethod
    async def sync_campaigns_for_user(
        *,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        # Get token
        result = await db.execute(
            select(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
        )
        token = result.scalar_one_or_none()

        if not token:
            raise RuntimeError("Meta account not connected")

        # Get user's ad accounts
        result = await db.execute(
            select(MetaAdAccount)
            .join(UserMetaAdAccount)
            .where(UserMetaAdAccount.user_id == user_id)
        )
        ad_accounts = result.scalars().all()

        total = 0

        async with httpx.AsyncClient(timeout=20) as client:
            for acct in ad_accounts:
                response = await client.get(
                    f"{META_GRAPH_BASE}/{acct.meta_account_id}/campaigns",
                    params={
                        "access_token": token.access_token,
                        "fields": "id,name,objective,status",
                    },
                )
                response.raise_for_status()

                for c in response.json().get("data", []):
                    result = await db.execute(
                        select(Campaign).where(
                            Campaign.meta_campaign_id == c["id"]
                        )
                    )
                    campaign = result.scalar_one_or_none()

                    if not campaign:
                        db.add(
                            Campaign(
                                meta_campaign_id=c["id"],
                                ad_account_id=acct.id,
                                name=c["name"],
                                objective=c["objective"],
                                status=c["status"],
                                ai_active=False,
                                created_at=datetime.utcnow(),
                            )
                        )
                    else:
                        campaign.name = c["name"]
                        campaign.status = c["status"]
                        campaign.last_meta_sync_at = datetime.utcnow()

                    total += 1

        await db.commit()
        return total

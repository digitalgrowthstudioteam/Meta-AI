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
from app.plans.enforcement import EnforcementError


META_GRAPH_BASE = "https://graph.facebook.com/v19.0"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


# =====================================================
# 🔒 GLOBAL META SYNC KILL SWITCH
# =====================================================
def assert_meta_sync_enabled():
    """
    Hard kill switch for ALL Meta interactions.
    Controlled by admin global setting.
    """
    if not getattr(settings, "META_SYNC_ENABLED", True):
        raise EnforcementError(
            code="META_SYNC_DISABLED",
            message="Meta sync is temporarily disabled by admin.",
            action="CONTACT_ADMIN",
        )


class MetaOAuthService:
    """
    Handles Meta OAuth token exchange & storage.
    """

    @staticmethod
    async def _exchange_for_long_lived_token(short_token: str) -> dict:
        assert_meta_sync_enabled()

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
        assert_meta_sync_enabled()

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
    HARDENED + KILL-SWITCHED
    """

    @staticmethod
    async def sync_user_ad_accounts(
        *,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        assert_meta_sync_enabled()

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

        result = await db.execute(
            select(UserMetaAdAccount)
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
            )
        )
        has_selected = result.scalar_one_or_none() is not None

        processed = 0
        first_account_id = None

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

            if first_account_id is None:
                first_account_id = meta_account.id

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
                        is_selected=False,
                    )
                )

            processed += 1

        if not has_selected and first_account_id:
            await db.execute(
                update(UserMetaAdAccount)
                .where(UserMetaAdAccount.user_id == user_id)
                .values(is_selected=False)
            )
            await db.execute(
                update(UserMetaAdAccount)
                .where(
                    UserMetaAdAccount.user_id == user_id,
                    UserMetaAdAccount.meta_ad_account_id == first_account_id,
                )
                .values(is_selected=True)
            )

        await db.commit()
        return processed


class MetaCampaignService:
    """
    Read-only Meta Campaign sync.
    HARDENED + KILL-SWITCHED
    """

    @staticmethod
    async def sync_campaigns_for_user(
        *,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        assert_meta_sync_enabled()

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

        result = await db.execute(
            select(MetaAdAccount)
            .join(UserMetaAdAccount)
            .where(
                UserMetaAdAccount.user_id == user_id,
                UserMetaAdAccount.is_selected.is_(True),
            )
            .limit(1)
        )
        ad_account = result.scalar_one_or_none()

        if not ad_account:
            return 0

        total = 0

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    f"{META_GRAPH_BASE}/{ad_account.meta_account_id}/campaigns",
                    params={
                        "access_token": token.access_token,
                        "fields": "id,name,objective,status",
                    },
                )
                response.raise_for_status()

                for c in response.json().get("data", []):
                    result = await db.execute(
                        select(Campaign).where(
                            Campaign.meta_campaign_id == c["id"],
                            Campaign.ad_account_id == ad_account.id,
                        )
                    )
                    campaign = result.scalar_one_or_none()

                    if not campaign:
                        db.add(
                            Campaign(
                                meta_campaign_id=c["id"],
                                ad_account_id=ad_account.id,
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

        except Exception:
            await db.rollback()
            return 0

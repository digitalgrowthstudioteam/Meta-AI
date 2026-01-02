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
from app.core.config import settings


META_GRAPH_BASE = "https://graph.facebook.com/v19.0"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"


class MetaOAuthService:
    """
    Handles Meta OAuth token exchange & storage.
    Enforces:
    - Long-lived tokens only
    - One active token per user
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

        # -------------------------------------------------
        # 1. Exchange code → short-lived token
        # -------------------------------------------------
        short_token_data = await exchange_code_for_token(code)
        short_token = short_token_data["access_token"]

        # -------------------------------------------------
        # 2. Exchange short → long-lived token (60 days)
        # -------------------------------------------------
        long_token_data = await MetaOAuthService._exchange_for_long_lived_token(
            short_token
        )

        expires_in = long_token_data.get("expires_in")
        expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in)
            if expires_in
            else None
        )

        # -------------------------------------------------
        # 3. Revoke existing active tokens for user
        # -------------------------------------------------
        await db.execute(
            update(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
            .values(is_active=False)
        )

        # -------------------------------------------------
        # 4. Store new long-lived token
        # -------------------------------------------------
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
        """
        Fetch Meta ad accounts for the user and sync globally.
        Returns number of accounts processed.
        """

        # -------------------------------------------------
        # 1. Get active Meta OAuth token
        # -------------------------------------------------
        result = await db.execute(
            select(MetaOAuthToken)
            .where(
                MetaOAuthToken.user_id == user_id,
                MetaOAuthToken.is_active.is_(True),
            )
            .order_by(MetaOAuthToken.created_at.desc())
        )
        token = result.scalar_one_or_none()

        if not token:
            raise RuntimeError("Meta account not connected")

        # -------------------------------------------------
        # 2. Fetch ad accounts from Meta
        # -------------------------------------------------
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

        ad_accounts = data.get("data", [])

        # -------------------------------------------------
        # 3. Upsert accounts + access mapping
        # -------------------------------------------------
        processed = 0

        for acct in ad_accounts:
            meta_account_id = acct["id"]
            account_name = acct.get("name", "")

            # ---- GLOBAL ACCOUNT UPSERT ----
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
            else:
                if meta_account.account_name != account_name:
                    meta_account.account_name = account_name

            # ---- USER ACCESS MAPPING ----
            result = await db.execute(
                select(UserMetaAdAccount).where(
                    UserMetaAdAccount.user_id == user_id,
                    UserMetaAdAccount.meta_ad_account_id == meta_account.id,
                )
            )
            access = result.scalar_one_or_none()

            if not access:
                access = UserMetaAdAccount(
                    user_id=user_id,
                    meta_ad_account_id=meta_account.id,
                    role="owner",
                )
                db.add(access)

            processed += 1

        await db.commit()
        return processed

from datetime import datetime
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_api.models import (
    MetaOAuthToken,
    MetaAdAccount,
    UserMetaAdAccount,
)
from app.core.config import settings


META_GRAPH_BASE = "https://graph.facebook.com/v19.0"


class MetaOAuthService:
    """
    Handles Meta OAuth token exchange & storage.
    """

    @staticmethod
    async def store_token(
        db: AsyncSession,
        *,
        user_id: UUID,
        code: str,
    ) -> MetaOAuthToken:
        from app.meta_api.oauth import exchange_code_for_token

        token_data = await exchange_code_for_token(code)

        expires_in = token_data.get("expires_in")
        expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in)
            if expires_in
            else None
        )

        token = MetaOAuthToken(
            user_id=user_id,
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type"),
            expires_at=expires_at,
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

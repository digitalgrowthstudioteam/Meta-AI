from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.meta_api.models import MetaOAuthToken
from app.meta_api.oauth import exchange_code_for_token


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

"""
Session Context Routes
SINGLE SOURCE OF TRUTH for frontend state

Exposes:
- GET /api/session/context

Rules:
- Read-only
- Cookie-based auth
- Used by ALL frontend pages
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount

router = APIRouter(
    prefix="/session",
    tags=["Session Context"],
)


@router.get("/context")
async def session_context(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    GLOBAL SESSION CONTEXT
    - Authenticated user
    - Exactly ONE selected Meta ad account
    """

    result = await db.execute(
        select(MetaAdAccount)
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.is_selected.is_(True),
        )
    )
    ad_account = result.scalar_one_or_none()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.role == "admin",
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        "ad_account": (
            {
                "id": str(ad_account.id),
                "name": ad_account.account_name,
                "meta_account_id": ad_account.meta_account_id,
            }
            if ad_account
            else None
        ),
    }

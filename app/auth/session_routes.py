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
    Returns:
    - Authenticated user
    - List of ALL linked Meta ad accounts
    - Exactly ONE active (selected) Meta ad account if exists
    """

    # Fetch all linked ad accounts for this user
    result = await db.execute(
        select(
            MetaAdAccount.id,
            MetaAdAccount.account_name,
            MetaAdAccount.meta_account_id,
            UserMetaAdAccount.is_selected,
        )
        .join(
            UserMetaAdAccount,
            UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id,
        )
        .where(UserMetaAdAccount.user_id == user.id)
        .order_by(MetaAdAccount.account_name)
    )

    rows = result.all()

    # Transform rows → list
    ad_accounts = [
        {
            "id": str(r.id),
            "name": r.account_name,
            "meta_account_id": r.meta_account_id,
            "is_selected": r.is_selected,
        }
        for r in rows
    ]

    # Identify active ad account (if any)
    active = next((a for a in ad_accounts if a["is_selected"]), None)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.role == "admin",
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        # New fields for FE multi-account support
        "ad_accounts": ad_accounts,
        "active_ad_account_id": active["id"] if active else None,

        # Backward compatibility field for old UI (optional)
        "ad_account": (
            {
                "id": active["id"],
                "name": active["name"],
                "meta_account_id": active["meta_account_id"],
            }
            if active
            else None
        ),
    }

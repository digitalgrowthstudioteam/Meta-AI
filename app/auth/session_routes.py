"""
Session Context Routes
SINGLE SOURCE OF TRUTH for frontend state

Exposes:
- GET /api/session/context
- POST /api/session/set-active

Rules:
- Cookie-based auth
- Used by ALL frontend pages
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

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

    ad_accounts = [
        {
            "id": str(r.id),
            "name": r.account_name,
            "meta_account_id": r.meta_account_id,
            "is_selected": r.is_selected,
        }
        for r in rows
    ]

    active = next((a for a in ad_accounts if a["is_selected"]), None)

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_admin": user.role == "admin",
            "is_impersonated": getattr(user, "_is_impersonated", False),
        },
        "ad_accounts": ad_accounts,
        "active_ad_account_id": active["id"] if active else None,
        "ad_account": (
            {
                "id": active["id"],
                "name": active["name"],
                "meta_account_id": active["meta_account_id"],
            }
            if active else None
        ),
    }


@router.post("/set-active")
async def set_active_ad_account(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Switch currently active Meta Ad Account for this user.
    Body: { "account_id": "<uuid>" }
    """

    account_id = payload.get("account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id required")

    # Verify that account belongs to this user
    result = await db.execute(
        select(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.meta_ad_account_id == account_id,
        )
    )
    relation = result.scalar_one_or_none()

    if not relation:
        raise HTTPException(status_code=403, detail="Not authorized to select this account")

    # 1) Set all accounts to false
    await db.execute(
        update(UserMetaAdAccount)
        .where(UserMetaAdAccount.user_id == user.id)
        .values(is_selected=False)
    )

    # 2) Set selected account to true
    await db.execute(
        update(UserMetaAdAccount)
        .where(
            UserMetaAdAccount.user_id == user.id,
            UserMetaAdAccount.meta_ad_account_id == account_id,
        )
        .values(is_selected=True)
    )

    await db.commit()

    # Return updated context
    return await session_context(db=db, user=user)


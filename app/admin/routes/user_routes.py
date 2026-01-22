from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.plans.subscription_models import Subscription
from app.billing.invoice_models import Invoice
from app.campaigns.models import Campaign
from app.meta_api.models import MetaAdAccount, UserMetaAdAccount

from app.admin.rbac import assert_admin_permission


router = APIRouter()

ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}


def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =====================================================
# USERS LIST
# =====================================================
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:read")

    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    response = []

    for u in users:
        sub_status = await db.scalar(
            select(Subscription.status)
            .where(Subscription.user_id == u.id)
            .order_by(Subscription.created_at.desc())
            .limit(1)
        )

        response.append(
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "last_login_at": (
                    u.last_login_at.isoformat() if getattr(u, "last_login_at", None) else None
                ),
                "subscription_status": sub_status,
                "ai_campaigns_active": 0,  # future patchable
            }
        )

    return response


# =====================================================
# USER DETAIL
# =====================================================
@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:read")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Meta Accounts
    meta_stmt = (
        select(MetaAdAccount)
        .join(UserMetaAdAccount, UserMetaAdAccount.meta_ad_account_id == MetaAdAccount.id)
        .where(UserMetaAdAccount.user_id == user_id)
        .order_by(MetaAdAccount.connected_at.desc())
    )
    meta_res = await db.execute(meta_stmt)
    meta_accounts = [
        {
            "id": str(m.id),
            "name": m.account_name,
            "status": "active" if m.is_active else "inactive",
            "last_sync_at": None,
        }
        for m in meta_res.scalars().all()
    ]

    # Campaigns
    camp_stmt = select(Campaign).order_by(Campaign.created_at.desc())
    camp_res = await db.execute(camp_stmt)
    campaigns = [
        {
            "id": str(c.id),
            "name": c.name,
            "objective": c.objective,
            "ai_active": c.ai_active,
            "status": c.status,
            "last_ai_action_at": None,
        }
        for c in camp_res.scalars().all()
    ]

    # Invoices
    inv_stmt = (
        select(Invoice)
        .where(Invoice.user_id == user.id)
        .order_by(Invoice.created_at.desc())
        .limit(50)
    )
    inv_res = await db.execute(inv_stmt)
    invoices = [
        {
            "id": str(i.id),
            "amount": i.total_amount,
            "status": i.status,
            "created_at": i.created_at.isoformat(),
        }
        for i in inv_res.scalars().all()
    ]

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login_at": (
                user.last_login_at.isoformat() if user.last_login_at else None
            ),
        },
        "meta_accounts": meta_accounts,
        "campaigns": campaigns,
        "invoices": invoices,
        "ai_actions": [],
    }


# =====================================================
# PHASE 10 — USAGE OVERRIDES
# =====================================================
from app.admin.schemas import (
    UsageOverrideUpsert,
    UsageOverrideDelete,
)
from app.plans.override_service import UsageOverrideService


# GET CURRENT OVERRIDES
@router.get("/users/{user_id}/usage")
async def get_user_usage_overrides(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:read")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    overrides = await UsageOverrideService.get_overrides_for_user(
        db=db,
        user_id=user_id,
    )
    return overrides


# UPSERT OVERRIDE
@router.post("/users/{user_id}/usage")
async def upsert_user_usage_override(
    user_id: UUID,
    payload: UsageOverrideUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    override = await UsageOverrideService.upsert_override(
        db=db,
        admin_user_id=current_user.id,
        user_id=user_id,
        key=payload.key,
        value=payload.value,
        expires_at=payload.expires_at,
        reason=payload.reason,
    )

    return {
        "key": override.key,
        "value": override.value,
        "expires_at": override.expires_at,
        "updated_by": str(override.updated_by) if override.updated_by else None,
        "updated_at": override.updated_at.isoformat() if override.updated_at else None,
    }


# DELETE OVERRIDE
@router.delete("/users/{user_id}/usage")
async def delete_user_usage_override(
    user_id: UUID,
    payload: UsageOverrideDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await UsageOverrideService.delete_override(
        db=db,
        admin_user_id=current_user.id,
        user_id=user_id,
        key=payload.key,
        reason=payload.reason,
    )
    return {"status": "deleted"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.admin.service import AdminOverrideService
from app.admin.rbac import assert_admin_permission

router = APIRouter()


ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}


def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# RISK DASHBOARD
# =========================
@router.get("/risk")
async def get_risk_dashboard(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return {
        "high_risk_users": 0,
        "flagged_campaigns": 0,
        "status": "secure"
    }


@router.get("/risk/timeline")
async def get_risk_timeline(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return []


@router.get("/risk/alerts")
async def get_risk_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    stmt = select(User).where(User.is_active == False).limit(20)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return [
        {
            "user_id": str(u.id),
            "email": u.email,
            "reason": "Account Inactive/Frozen",
            "detected_at": datetime.utcnow().isoformat()
        }
        for u in users
    ]


# =========================
# RISK ACTIONS
# =========================
@router.post("/risk/freeze-user")
async def risk_freeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")

    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(status_code=400, detail="user_id and reason required")

    await AdminOverrideService.freeze_user(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )

    return {"status": "user_frozen"}


@router.post("/risk/unfreeze-user")
async def risk_unfreeze_user(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")

    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(status_code=400, detail="user_id and reason required")

    await AdminOverrideService.unfreeze_user(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )

    return {"status": "user_unfrozen"}


@router.post("/risk/disable-user-ai")
async def risk_disable_user_ai(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="users:write")

    user_id = payload.get("user_id")
    reason = payload.get("reason")
    if not user_id or not reason:
        raise HTTPException(status_code=400, detail="user_id and reason required")

    await AdminOverrideService.disable_user_ai(
        db=db, admin_user_id=current_user.id, target_user_id=UUID(user_id), reason=reason
    )

    return {"status": "ai_disabled_for_user"}

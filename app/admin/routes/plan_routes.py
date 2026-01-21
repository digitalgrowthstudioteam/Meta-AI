from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.admin.rbac import assert_admin_permission
from app.plans.models import Plan

router = APIRouter(prefix="/plans", tags=["Admin Plans"])

ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}

def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("")
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:read")

    result = await db.execute(
        Plan.__table__.select().order_by(Plan.id.asc())
    )
    rows = result.fetchall()

    return [
        {
            "id": r.id,
            "name": r.name,
            "code": r.name.lower(),
            "monthly_price": r.monthly_price,
            "yearly_price": r.yearly_price,
            "max_ad_accounts": r.max_ad_accounts,
            "max_ai_campaigns": r.max_ai_campaigns,
            "yearly_allowed": r.yearly_allowed,
            "is_hidden": r.is_hidden,
            "is_active": r.is_active,
        }
        for r in rows
    ]


@router.post("/{plan_id}")
async def update_plan(
    plan_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="billing:write")

    result = await db.get(Plan, plan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found")

    if "monthly_price" in payload:
        result.monthly_price = int(payload["monthly_price"])

    if "yearly_price" in payload:
        result.yearly_price = int(payload["yearly_price"]) if payload["yearly_price"] else None

    if "max_ad_accounts" in payload:
        result.max_ad_accounts = int(payload["max_ad_accounts"])

    if "max_ai_campaigns" in payload:
        result.max_ai_campaigns = int(payload["max_ai_campaigns"])

    await db.commit()
    return {"status": "ok"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.admin.plan_service import PlanService
from app.core.config import settings

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
    plans = await PlanService.list_plans(db)

    currency = settings.BILLING_CURRENCY or "INR"

    return [
        {
            "id": p.id,
            "name": p.name,
            "code": p.name.lower().replace(" ", "_"),
            "monthly_price": p.monthly_price,
            "yearly_price": p.yearly_price,
            "max_ad_accounts": p.max_ad_accounts,
            "max_ai_campaigns": p.max_ai_campaigns,
            "is_active": p.is_active,
            "is_hidden": p.is_hidden,
            "auto_allowed": p.auto_allowed,
            "manual_allowed": p.manual_allowed,
            "yearly_allowed": p.yearly_allowed,
            "currency": currency,
        }
        for p in plans
    ]


@router.post("/{plan_id}")
async def update_plan(
    plan_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    await PlanService.update_plan(db, plan_id, payload)
    return {"status": "ok"}

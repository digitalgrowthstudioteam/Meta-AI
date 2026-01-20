from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.admin.rbac import assert_admin_permission
from app.admin.pricing_service import AdminPricingConfigService

router = APIRouter()


ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}


def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# PRICING CONFIG - ACTIVE
# =========================
@router.get("/pricing-config/active")
async def get_active_pricing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return await AdminPricingConfigService.get_active_config(db)


# =========================
# PRICING CONFIG - LIST
# =========================
@router.get("/pricing-config")
async def list_pricing_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    configs = await AdminPricingConfigService.list_configs(db)
    return configs

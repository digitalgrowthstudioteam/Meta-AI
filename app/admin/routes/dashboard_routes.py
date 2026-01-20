from fastapi import APIRouter, Depends
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User

from app.admin.service import AdminOverrideService
from app.admin.rbac import assert_admin_permission

router = APIRouter()


ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}


def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# DASHBOARD
# =========================
@router.get("/dashboard")
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:read")
    return await AdminOverrideService.get_dashboard_stats(db=db)


# =========================
# METRIC SYNC STATUS
# =========================
@router.get("/metrics/sync-status")
async def get_metrics_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return {
        "status": "healthy",
        "last_sync": datetime.utcnow().isoformat(),
        "pending_accounts": 0
    }


# =========================
# REPORTS
# =========================
@router.get("/reports")
async def list_admin_reports(
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    return []

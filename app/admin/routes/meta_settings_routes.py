# app/admin/routes/meta_settings_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.admin.models import GlobalSettings
from app.admin.service import AdminOverrideService

router = APIRouter(prefix="/admin/global-settings", tags=["Admin Meta Settings"])


# =========================
# ADMIN GUARD
# =========================
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# GET CURRENT META SETTINGS
# =========================
@router.get("")
async def get_meta_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    settings = await AdminOverrideService.get_global_settings(db)
    return {
        "meta_sync_enabled": settings.meta_sync_enabled,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "updated_at": settings.updated_at.isoformat(),
    }


# =========================
# UPDATE META SETTINGS
# =========================
@router.put("")
async def update_meta_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    updates = {}
    for key in ["meta_sync_enabled", "ai_globally_enabled", "maintenance_mode"]:
        if key in payload:
            updates[key] = payload[key]

    if not updates:
        raise HTTPException(400, detail="No valid settings provided to update")

    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, detail="Reason is required for auditing")

    settings = await AdminOverrideService.update_global_settings(
        db=db,
        admin_user_id=current_user.id,
        updates=updates,
        reason=reason,
    )

    return {
        "meta_sync_enabled": settings.meta_sync_enabled,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "updated_at": settings.updated_at.isoformat(),
    }

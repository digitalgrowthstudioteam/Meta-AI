from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
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
# META SETTINGS (GET)
# =========================
@router.get("/meta-settings")
async def get_meta_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:read")

    settings = await AdminOverrideService.get_global_settings(db)
    return {
        "meta_sync_enabled": settings.meta_sync_enabled,
        "ai_globally_enabled": settings.ai_globally_enabled,
        "maintenance_mode": settings.maintenance_mode,
        "site_name": settings.site_name,
        "dashboard_title": settings.dashboard_title,
        "logo_url": settings.logo_url,
        "expansion_mode_enabled": settings.expansion_mode_enabled,
        "fatigue_mode_enabled": settings.fatigue_mode_enabled,
        "auto_pause_enabled": settings.auto_pause_enabled,
        "confidence_gating_enabled": settings.confidence_gating_enabled,
        "max_optimizations_per_day": settings.max_optimizations_per_day,
        "max_expansions_per_day": settings.max_expansions_partner_day,
        "ai_refresh_frequency_minutes": settings.ai_refresh_frequency_minutes,
    }


# =========================
# META SETTINGS (POST)
# =========================
@router.post("/meta-settings")
async def update_meta_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    assert_admin_permission(admin_user=current_user, permission="system:write")
    forbid_impersonated_writes(current_user)

    allowed_fields = [
        "meta_sync_enabled", "ai_globally_enabled", "maintenance_mode",
        "site_name", "dashboard_title", "logo_url", "expansion_mode_enabled",
        "fatigue_mode_enabled", "auto_pause_enabled", "confidence_gating_enabled",
        "max_optimizations_per_day", "max_expansions_per_day", "ai_refresh_frequency_minutes",
    ]

    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    reason = payload.get("reason")

    if not updates or not reason:
        raise HTTPException(status_code=400, detail="Updates and reason are required")

    await AdminOverrideService.update_global_settings(
        db=db,
        admin_user_id=current_user.id,
        updates=updates,
        reason=reason,
    )

    return {"status": "updated"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.admin.schemas import (
    AdminOverrideCreate,
    AdminOverrideResponse,
)
from app.admin.service import AdminOverrideService

router = APIRouter(prefix="/admin/overrides", tags=["Admin"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/", response_model=AdminOverrideResponse)
async def create_override(
    payload: AdminOverrideCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    override = await AdminOverrideService.create_override(
        db=db,
        user_id=payload.user_id,
        extra_ai_campaigns=payload.extra_ai_campaigns,
        force_ai_enabled=payload.force_ai_enabled,
        override_expires_at=payload.override_expires_at,
        reason=payload.reason,
    )

    return override


@router.get("/", response_model=list[AdminOverrideResponse])
async def list_overrides(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)
    return await AdminOverrideService.list_overrides(db)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.plans.enforcement import PlanEnforcementService

router = APIRouter(prefix="/admin/ai-limit", tags=["Admin AI Limits"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/user/{user_id}")
async def ai_limit_status_for_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)

    status = await PlanEnforcementService.get_ai_limit_status(db=db, user_id=user_id)
    return status

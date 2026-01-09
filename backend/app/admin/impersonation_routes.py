from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_admin
from app.users.models import User
from app.campaigns.models import CampaignActionLog

router = APIRouter(
    prefix="/admin",
    tags=["Admin Impersonation"],
)


@router.post("/impersonate")
async def impersonate_user(
    *,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot impersonate self",
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Target user not found",
        )

    # AUDIT LOG — impersonation start
    db.add(
        CampaignActionLog(
            campaign_id=None,
            user_id=admin_user.id,
            actor_type="admin",
            action_type="impersonation_start",
            before_state={
                "admin_user_id": str(admin_user.id),
                "admin_email": admin_user.email,
            },
            after_state={
                "impersonated_user_id": str(target_user.id),
                "impersonated_email": target_user.email,
                "mode": "read_only",
            },
            reason="Admin impersonation (read-only)",
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()

    return {
        "status": "impersonation_started",
        "mode": "read_only",
        "impersonated_user": {
            "id": str(target_user.id),
            "email": target_user.email,
        },
        "started_at": datetime.utcnow().isoformat(),
    }


@router.post("/impersonate/exit")
async def exit_impersonation(
    *,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    # AUDIT LOG — impersonation end
    db.add(
        CampaignActionLog(
            campaign_id=None,
            user_id=admin_user.id,
            actor_type="admin",
            action_type="impersonation_end",
            before_state={},
            after_state={},
            reason="Admin exited impersonation",
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()

    return {
        "status": "impersonation_ended",
        "ended_at": datetime.utcnow().isoformat(),
    }

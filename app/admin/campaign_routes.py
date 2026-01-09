from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.campaigns.models import Campaign

router = APIRouter(prefix="/admin/campaigns", tags=["Admin Campaigns"])


@router.get("")
async def list_admin_campaigns(
    ai_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    if current_user.role != "admin":
        return []

    stmt = select(Campaign)

    if ai_active is not None:
        stmt = stmt.where(Campaign.ai_active.is_(ai_active))

    result = await db.execute(stmt)
    campaigns = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "user_id": str(c.user_id),
            "name": c.name,
            "objective": c.objective,
            "status": c.status,
            "ai_active": c.ai_active,
            "ai_execution_locked": c.ai_execution_locked,
            "is_manual": c.is_manual,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]

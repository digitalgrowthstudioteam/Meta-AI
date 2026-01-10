from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog

router = APIRouter(prefix="/admin/ai", tags=["Admin AI Force Actions"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.post("/deactivate/{campaign_id}")
async def admin_force_deactivate_ai(
    campaign_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
):
    require_admin(current_user)
    forbid_impersonated_writes(current_user)

    reason = payload.get("reason")
    if not reason:
        raise HTTPException(400, "Reason required")

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    if not campaign.ai_active:
        return {"status": "already_inactive"}

    before_state = {"ai_active": True}

    campaign.ai_active = False
    campaign.ai_deactivated_at = datetime.utcnow()

    after_state = {"ai_active": False}

    db.add(
        CampaignActionLog(
            campaign_id=campaign.id,
            user_id=current_user.id,
            actor_type="admin",
            action_type="force_ai_deactivate",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
        )
    )

    await db.commit()
    await db.refresh(campaign)

    return {"status": "deactivated", "campaign_id": str(campaign.id)}

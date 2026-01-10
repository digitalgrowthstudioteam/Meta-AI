from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db_session import get_db
from app.users.models import User
from app.campaigns.models import Campaign, CampaignActionLog
from app.auth.dependencies import require_user, forbid_impersonated_writes


router = APIRouter(prefix="/admin/campaigns", tags=["Admin Campaigns"])


# -------------------------------------
# ADMIN GUARD
# -------------------------------------
def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# -------------------------------------
# LIST CAMPAIGNS (READ)
# -------------------------------------
@router.get("", status_code=status.HTTP_200_OK)
async def admin_list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
    user_id: UUID | None = Query(None),
    ai_active: bool | None = Query(None),
):
    require_admin(current_user)

    stmt = select(Campaign)

    if user_id:
        stmt = stmt.where(Campaign.user_id == user_id)

    if ai_active is not None:
        stmt = stmt.where(Campaign.ai_active.is_(ai_active))

    result = await db.execute(stmt.order_by(Campaign.created_at.desc()))
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


# -------------------------------------
# FORCE TOGGLE AI (WRITE + AUDIT)
# -------------------------------------
@router.post("/{campaign_id}/force-ai", status_code=status.HTTP_200_OK)
async def admin_force_toggle_ai(
    campaign_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(forbid_impersonated_writes),
):
    require_admin(current_user)

    enable = payload.get("enable")
    reason = payload.get("reason")

    if enable is None or not reason:
        raise HTTPException(400, "enable and reason required")

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    before_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    # Apply change
    campaign.ai_active = bool(enable)
    campaign.ai_execution_locked = False if enable else True
    campaign.ai_activated_at = datetime.utcnow() if enable else None
    campaign.ai_deactivated_at = None if enable else datetime.utcnow()

    after_state = {
        "ai_active": campaign.ai_active,
        "ai_execution_locked": campaign.ai_execution_locked,
    }

    # Audit log
    db.add(
        CampaignActionLog(
            campaign_id=campaign.id,
            user_id=current_user.id,
            actor_type="admin",
            action_type="force_ai_toggle",
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_at=datetime.utcnow(),
        )
    )

    await db.commit()

    return {
        "status": "ok",
        "campaign_id": str(campaign.id),
        "ai_active": campaign.ai_active,
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, timedelta

from app.core.db_session import get_db
from app.auth.dependencies import require_user, forbid_impersonated_writes
from app.users.models import User
from app.plans.subscription_models import SubscriptionAddon
from app.admin.models import AdminAuditLog

router = APIRouter(prefix="/slots", tags=["Admin Slots"])

def require_admin(user: User):
if user.role != "admin":
raise HTTPException(status_code=403, detail="Admin access required")
return user

async def _get_slot_or_404(db: AsyncSession, slot_id: UUID) -> SubscriptionAddon:
result = await db.execute(
select(SubscriptionAddon).where(SubscriptionAddon.id == slot_id)
)
slot = result.scalar_one_or_none()
if not slot:
raise HTTPException(status_code=404, detail="Slot addon not found")
return slot

async def _audit(
*,
db: AsyncSession,
admin_user: User,
slot: SubscriptionAddon,
action: str,
before_state: dict,
after_state: dict,
reason: str,
):
db.add(
AdminAuditLog(
admin_user_id=admin_user.id,
target_type="subscription_addon",
target_id=slot.id,
action=action,
before_state=before_state,
after_state=after_state,
reason=reason,
created_at=datetime.utcnow(),
)
)
await db.commit()

@router.post("/{slot_id}/extend")
async def extend_slot(
slot_id: UUID,
payload: dict,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)
forbid_impersonated_writes(current_user)

```
days = payload.get("days")
reason = payload.get("reason")

if not days or days <= 0 or not reason:
    raise HTTPException(400, "days and reason required")

slot = await _get_slot_or_404(db, slot_id)

before = {"expires_at": slot.expires_at.isoformat()}
slot.expires_at = slot.expires_at + timedelta(days=int(days))
after = {"expires_at": slot.expires_at.isoformat()}

await _audit(
    db=db,
    admin_user=current_user,
    slot=slot,
    action="slot_extend",
    before_state=before,
    after_state=after,
    reason=reason,
)

return {"status": "extended", "expires_at": slot.expires_at}
```

@router.post("/{slot_id}/expire")
async def expire_slot(
slot_id: UUID,
payload: dict,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)
forbid_impersonated_writes(current_user)

```
reason = payload.get("reason")
if not reason:
    raise HTTPException(400, "reason required")

slot = await _get_slot_or_404(db, slot_id)

before = {"expires_at": slot.expires_at.isoformat()}
slot.expires_at = datetime.utcnow()
after = {"expires_at": slot.expires_at.isoformat()}

await _audit(
    db=db,
    admin_user=current_user,
    slot=slot,
    action="slot_force_expire",
    before_state=before,
    after_state=after,
    reason=reason,
)

return {"status": "expired"}
```

@router.post("/{slot_id}/adjust")
async def adjust_slot_quantity(
slot_id: UUID,
payload: dict,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(require_user),
):
require_admin(current_user)
forbid_impersonated_writes(current_user)

```
qty = payload.get("extra_ai_campaigns")
reason = payload.get("reason")

if qty is None or qty < 0 or not reason:
    raise HTTPException(400, "extra_ai_campaigns and reason required")

slot = await _get_slot_or_404(db, slot_id)

before = {"extra_ai_campaigns": slot.extra_ai_campaigns}
slot.extra_ai_campaigns = int(qty)
after = {"extra_ai_campaigns": slot.extra_ai_campaigns}

await _audit(
    db=db,
    admin_user=current_user,
    slot=slot,
    action="slot_adjust_quantity",
    before_state=before,
    after_state=after,
    reason=reason,
)

return {
    "status": "adjusted",
    "extra_ai_campaigns": slot.extra_ai_campaigns,
}

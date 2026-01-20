from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_user
from app.users.models import User
from app.admin.models import AdminAuditLog
from app.admin.rbac import assert_admin_permission

router = APIRouter()


ALLOWED_ADMIN_ROLES = {"admin", "super_admin", "support_admin", "billing_admin"}


def require_admin(user: User):
    if user.role not in ALLOWED_ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# =========================
# AUDIT LOGS
# =========================
@router.get("/audit/actions")
async def list_admin_audit_logs(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_user),
    target_type: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    require_admin(current_user)

    stmt = select(AdminAuditLog)

    if target_type:
        stmt = stmt.where(AdminAuditLog.target_type == target_type)
    if action:
        stmt = stmt.where(AdminAuditLog.action == action)

    result = await db.execute(
        stmt.order_by(AdminAuditLog.created_at.desc()).limit(limit)
    )

    logs = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "admin_user_id": str(l.admin_user_id),
            "target_type": l.target_type,
            "target_id": str(l.target_id) if l.target_id else None,
            "action": l.action,
            "reason": l.reason,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]

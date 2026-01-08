from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db_session import get_db
from app.auth.dependencies import require_admin
from app.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin Users"])


# =====================================
# GET USER LIST (LITE)
# =====================================
@router.get("/users")
async def admin_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = await db.execute(select(User.id, User.email, User.is_active))
    rows = result.all()

    return [
        {"id": str(r.id), "email": r.email, "is_active": r.is_active}
        for r in rows
    ]


# =====================================
# GET USER DETAILS
# =====================================
@router.get("/users/{user_id}")
async def admin_user_details(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


# =====================================
# TOGGLE USER ACTIVE STATUS
# =====================================
@router.post("/users/{user_id}/toggle")
async def admin_toggle_user_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_status = not user.is_active
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_active=new_status)
    )
    await db.commit()

    return {"status": "updated", "id": user_id, "is_active": new_status}

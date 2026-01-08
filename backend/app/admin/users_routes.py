from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db_session import get_db
from app.auth.dependencies import require_admin
from app.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin Users"])

@router.get("/users")
async def admin_users(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = await db.execute(select(User.id, User.email))
    rows = result.all()

    return [
        {"id": str(r.id), "email": r.email}
        for r in rows
    ]

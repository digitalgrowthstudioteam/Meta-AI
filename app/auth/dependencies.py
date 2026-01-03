from fastapi import Depends
from app.users.models import User

async def require_user() -> User:
    return User(
        id="dev-user",
        email="dev@local",
        role="admin",
        is_active=True,
    )

async def require_admin() -> User:
    return await require_user()

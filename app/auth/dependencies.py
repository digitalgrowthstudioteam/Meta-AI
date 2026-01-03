from fastapi import Depends
from app.users.models import User

# -----------------------------
# DEV MODE AUTH (TEMPORARY)
# -----------------------------

async def require_user() -> User:
    return User(
        id="dev-user",
        email="dev@local",
        role="admin",
        is_active=True,
    )

async def require_admin() -> User:
    return await require_user()

# -----------------------------
# COMPATIBILITY STUB
# DO NOT REMOVE
# -----------------------------
# Required because multiple backend routes
# still import get_current_user
async def get_current_user() -> User:
    return await require_user()

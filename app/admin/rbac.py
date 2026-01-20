from fastapi import HTTPException
from app.users.models import User

# =========================
# RBAC PERMISSION CHECKER
# =========================
def assert_admin_permission(*, admin_user: User, permission: str):
    """
    Simple RBAC for admin features.
    For now: role='admin' has all permissions.
    """
    if not admin_user or admin_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"Missing permission: {permission}"
        )
    
    return True

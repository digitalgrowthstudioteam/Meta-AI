from fastapi import HTTPException
from app.users.models import User

# =========================
# RBAC PERMISSION CHECKER
# =========================
def assert_admin_permission(user: User, required_permission: str):
    """
    Checks if the admin user has the specific required permission.
    For now, super admins (role='admin') have all permissions.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail=f"Missing permission: {required_permission}"
        )

    # In the future, we can add granular permission checks here.
    # For now, being an 'admin' grants everything.
    return True

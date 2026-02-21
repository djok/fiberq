from fastapi import Depends, HTTPException, status

from auth.kanidm import get_current_user
from auth.models import UserInfo


def require_role(*allowed_roles: str):
    """Factory for role-checking dependencies."""

    async def check_role(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if not set(allowed_roles).intersection(user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' or '.join(allowed_roles)}",
            )
        return user

    return check_role


require_admin = require_role("admin")
require_engineer_or_admin = require_role("admin", "engineer")
require_any_role = require_role("admin", "engineer", "field_worker")

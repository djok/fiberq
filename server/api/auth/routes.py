from fastapi import APIRouter, Depends

from auth.kanidm import get_current_user
from auth.models import UserInfo

router = APIRouter()


@router.get("/me", response_model=UserInfo)
async def get_me(user: UserInfo = Depends(get_current_user)):
    """Return current user info from Kanidm token."""
    return user


@router.get("/roles")
async def get_my_roles(user: UserInfo = Depends(get_current_user)):
    """Return current user's roles."""
    return {
        "sub": user.sub,
        "roles": user.roles,
        "is_admin": user.is_admin,
        "is_engineer": user.is_engineer,
        "is_field_worker": user.is_field_worker,
    }

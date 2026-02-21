from fastapi import APIRouter, Depends

from auth.kanidm import get_current_user
from auth.models import UserInfo
from database import get_pool

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


@router.post("/record-login")
async def record_login(user: UserInfo = Depends(get_current_user)):
    """Record a login event for the authenticated user."""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO user_logins (user_sub, username, last_login_at, login_source)
        VALUES ($1, $2, NOW(), 'web')
        ON CONFLICT (user_sub) DO UPDATE
        SET last_login_at = NOW(), login_source = 'web', username = $2
        """,
        user.sub,
        user.name,
    )
    return {"status": "recorded"}

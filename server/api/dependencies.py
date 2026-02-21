import asyncpg
from fastapi import Depends

from database import get_pool
from auth.zitadel import get_current_user, UserInfo


async def get_db() -> asyncpg.Pool:
    return get_pool()


async def require_admin(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if "admin" not in user.roles:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


async def require_engineer(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if not {"admin", "engineer"}.intersection(user.roles):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Engineer or admin role required")
    return user


async def require_field_worker(user: UserInfo = Depends(get_current_user)) -> UserInfo:
    if not {"admin", "engineer", "field_worker"}.intersection(user.roles):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Authentication required")
    return user

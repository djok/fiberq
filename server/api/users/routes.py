import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException

from auth.kanidm import get_current_user
from auth.models import UserInfo
from auth.roles import require_admin
from config import settings
from database import get_pool
from users.kanidm_client import KanidmAdminClient
from users.models import (
    CredentialResetOut,
    UserCreate,
    UserListOut,
    UserOut,
    UserRoleUpdate,
)

logger = logging.getLogger("fiberq.users")

router = APIRouter()

# Mapping of FiberQ role names -> Kanidm group names
FIBERQ_ROLE_GROUPS: dict[str, str] = {
    "admin": "fiberq_admin",
    "project_manager": "fiberq_project_manager",
    "engineer": "fiberq_engineer",
    "field_worker": "fiberq_field_worker",
}


def _get_kanidm_client() -> KanidmAdminClient:
    """Factory for Kanidm admin API client."""
    return KanidmAdminClient()


def _parse_person(person: dict, login_map: dict) -> UserOut:
    """Convert a Kanidm person dict into a UserOut model."""
    attrs = person.get("attrs", {})

    uuid = (attrs.get("uuid") or [None])[0]
    username = (attrs.get("name") or [""])[0]
    display_name = (attrs.get("displayname") or [""])[0]
    email = (attrs.get("mail") or [""])[0]
    phone = (attrs.get("phone") or [None])[0]
    is_active = "account_expire" not in attrs

    # Extract FiberQ roles from memberof groups
    memberof = attrs.get("memberof", [])
    roles = [
        g[len("fiberq_"):]
        for g in memberof
        if isinstance(g, str) and g.startswith("fiberq_")
    ]

    # Lookup last login by uuid or username
    last_login = login_map.get(uuid) or login_map.get(username)

    return UserOut(
        id=uuid or username,
        username=username,
        display_name=display_name,
        email=email,
        phone=phone,
        roles=roles,
        is_active=is_active,
        last_login=last_login,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=UserListOut)
async def list_users(user: UserInfo = Depends(require_admin)):
    """List all Kanidm person accounts with last login info."""
    kanidm = _get_kanidm_client()

    try:
        persons = await kanidm.list_persons()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    # Fetch last login timestamps from DB
    pool = get_pool()
    rows = await pool.fetch("SELECT user_sub, last_login_at FROM user_logins")
    login_map: dict = {row["user_sub"]: row["last_login_at"] for row in rows}

    users: list[UserOut] = []
    for person in persons:
        attrs = person.get("attrs", {})
        username = (attrs.get("name") or [""])[0]
        classes = attrs.get("class", [])

        # Filter out service accounts and system entries
        if "service_account" in classes:
            continue
        if username in ("anonymous",) or username.startswith("admin@"):
            continue

        users.append(_parse_person(person, login_map))

    return UserListOut(users=users)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, user: UserInfo = Depends(require_admin)):
    """Get a single user by Kanidm ID."""
    kanidm = _get_kanidm_client()

    try:
        person = await kanidm.get_person(user_id)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="User not found")
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    # Fetch last login for this user
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT user_sub, last_login_at FROM user_logins WHERE user_sub = $1",
        user_id,
    )
    login_map: dict = {row["user_sub"]: row["last_login_at"] for row in rows}

    return _parse_person(person, login_map)


@router.post("", response_model=CredentialResetOut, status_code=201)
async def create_user(body: UserCreate, user: UserInfo = Depends(require_admin)):
    """Create a new user in Kanidm and assign roles."""
    kanidm = _get_kanidm_client()

    try:
        await kanidm.create_person(body.username, body.display_name)

        if body.email:
            await kanidm.set_person_attr(body.username, "mail", [body.email])
        if body.phone:
            await kanidm.set_person_attr(body.username, "phone", [body.phone])

        for role in body.roles:
            group = FIBERQ_ROLE_GROUPS.get(role)
            if group:
                await kanidm.add_group_member(group, body.username)

        token = await kanidm.create_credential_reset_token(body.username, 3600)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            raise HTTPException(status_code=409, detail="Username already exists")
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    return CredentialResetOut(
        token=token,
        ttl=3600,
        reset_url=f"{settings.kanidm_url}/ui/reset",
    )


@router.post("/{user_id}/deactivate")
async def deactivate_user(user_id: str, user: UserInfo = Depends(require_admin)):
    """Deactivate a user by setting account_expire to epoch."""
    kanidm = _get_kanidm_client()

    try:
        await kanidm.deactivate_person(user_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    return {"status": "deactivated"}


@router.post("/{user_id}/reactivate")
async def reactivate_user(user_id: str, user: UserInfo = Depends(require_admin)):
    """Reactivate a user by removing account_expire."""
    kanidm = _get_kanidm_client()

    try:
        await kanidm.reactivate_person(user_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    return {"status": "reactivated"}


@router.put("/{user_id}/roles")
async def update_roles(
    user_id: str,
    body: UserRoleUpdate,
    user: UserInfo = Depends(require_admin),
):
    """Replace a user's FiberQ role group memberships."""
    kanidm = _get_kanidm_client()

    try:
        for role, group in FIBERQ_ROLE_GROUPS.items():
            if role in body.roles:
                await kanidm.add_group_member(group, user_id)
            else:
                try:
                    await kanidm.remove_group_member(group, user_id)
                except httpx.HTTPStatusError:
                    # Ignore errors when user is not a member of the group
                    pass
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    return {"status": "roles_updated", "roles": body.roles}


@router.post("/{user_id}/reset-password", response_model=CredentialResetOut)
async def reset_password(user_id: str, user: UserInfo = Depends(require_admin)):
    """Generate a credential reset token for a user."""
    kanidm = _get_kanidm_client()

    try:
        token = await kanidm.create_credential_reset_token(user_id, 3600)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Identity service error: {e}")

    return CredentialResetOut(
        token=token,
        ttl=3600,
        reset_url=f"{settings.kanidm_url}/ui/reset",
    )

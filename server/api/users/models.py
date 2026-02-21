from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    display_name: str
    email: str
    phone: str | None = None
    roles: list[str]  # e.g., ["admin", "project_manager"]


class UserRoleUpdate(BaseModel):
    roles: list[str]  # Full replacement list


class UserOut(BaseModel):
    id: str  # Kanidm UUID
    username: str
    display_name: str
    email: str
    phone: str | None = None
    roles: list[str]
    is_active: bool
    last_login: datetime | None = None


class UserListOut(BaseModel):
    users: list[UserOut]


class CredentialResetOut(BaseModel):
    token: str
    ttl: int
    reset_url: str  # {kanidm_url}/ui/reset

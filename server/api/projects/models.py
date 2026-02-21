from datetime import datetime

from pydantic import BaseModel

PROJECT_STATUSES = ["planning", "in_progress", "completed", "paused", "archived"]
PROJECT_ROLES = ["manager", "specialist", "observer"]


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    status: str = "planning"


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    member_count: int = 0
    member_names: list[str] = []
    extent: dict | None = None
    created_at: datetime
    created_by_sub: str | None


class ProjectMemberOut(BaseModel):
    id: int
    user_sub: str
    user_display_name: str | None
    user_email: str | None
    project_role: str
    assigned_at: datetime


class AssignMemberBody(BaseModel):
    user_sub: str
    user_display_name: str | None = None
    user_email: str | None = None
    project_role: str = "specialist"


class ProjectDetailOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    created_by_sub: str | None
    members: list[ProjectMemberOut] = []
    extent: dict | None = None


class ProjectStats(BaseModel):
    closures: int | None
    poles: int | None
    cables: int | None
    cable_length_m: float | None
    team_size: int
    last_sync_at: datetime | None
    last_sync_features: int | None


class ActivityEntry(BaseModel):
    event_type: str
    event_at: datetime
    user_sub: str | None
    user_display_name: str | None
    details: dict | None


class ActivityPage(BaseModel):
    entries: list[ActivityEntry]
    has_more: bool

from datetime import date, datetime

from pydantic import BaseModel


class WorkOrderCreate(BaseModel):
    title: str
    description: str = ""
    order_type: str  # installation, splice, repair, survey, maintenance
    priority: str = "medium"
    project_id: int
    due_date: date | None = None


class WorkOrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: date | None = None


class WorkOrderAssign(BaseModel):
    assigned_to_sub: str


class WorkOrderStatusChange(BaseModel):
    status: str  # created, assigned, in_progress, completed, verified, rejected


class WorkOrderOut(BaseModel):
    id: int
    title: str
    description: str | None
    order_type: str
    priority: str | None
    status: str
    project_id: int | None
    assigned_to_sub: str | None
    assigned_by_sub: str | None
    due_date: date | None
    created_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class WorkOrderItemCreate(BaseModel):
    item_type: str
    description: str = ""
    target_layer: str | None = None
    target_fid: int | None = None
    quantity: float | None = None
    unit: str | None = None


class WorkOrderItemOut(BaseModel):
    id: int
    work_order_id: int
    item_type: str
    description: str | None
    target_layer: str | None
    target_fid: int | None
    quantity: float | None
    unit: str | None
    status: str
    completed_at: datetime | None
    notes: str | None


class SMRReportCreate(BaseModel):
    work_order_id: int
    report_date: date | None = None
    weather: str = ""
    crew_size: int = 1
    hours_worked: float = 0
    activities: list[dict] = []
    materials_used: list[dict] = []
    issues: str = ""
    latitude: float | None = None
    longitude: float | None = None


class SMRReportOut(BaseModel):
    id: int
    work_order_id: int
    reported_by_sub: str | None
    report_date: date | None
    weather: str | None
    crew_size: int | None
    hours_worked: float | None
    activities: list | None
    materials_used: list | None
    issues: str | None

import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from database import get_pool
from auth.kanidm import get_current_user
from auth.models import UserInfo
from auth.roles import require_engineer_or_admin, require_any_role
from work_orders.models import (
    WorkOrderCreate, WorkOrderUpdate, WorkOrderAssign,
    WorkOrderStatusChange, WorkOrderOut,
    WorkOrderItemCreate, WorkOrderItemOut,
    SMRReportCreate, SMRReportOut,
)

router = APIRouter()

VALID_STATUSES = {"created", "assigned", "in_progress", "completed", "verified", "rejected"}
VALID_TRANSITIONS = {
    "created": {"assigned", "rejected"},
    "assigned": {"in_progress", "rejected"},
    "in_progress": {"completed", "rejected"},
    "completed": {"verified", "rejected"},
    "verified": set(),
    "rejected": {"created"},
}


# --- Work Orders -------------------------------------------------------------

@router.get("/", response_model=list[WorkOrderOut])
async def list_work_orders(
    project_id: int | None = None,
    status: str | None = None,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    query = """SELECT id, title, description, order_type, priority, status,
                      project_id, assigned_to_sub, assigned_by_sub,
                      due_date, created_at, started_at, completed_at
               FROM work_orders WHERE 1=1"""
    params = []
    idx = 1

    if project_id:
        query += f" AND project_id = ${idx}"
        params.append(project_id)
        idx += 1
    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1

    query += " ORDER BY created_at DESC"
    rows = await pool.fetch(query, *params)
    return [WorkOrderOut(**dict(r)) for r in rows]


@router.get("/my", response_model=list[WorkOrderOut])
async def my_work_orders(
    user: UserInfo = Depends(get_current_user),
):
    """Get work orders assigned to the current user."""
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, title, description, order_type, priority, status,
                  project_id, assigned_to_sub, assigned_by_sub,
                  due_date, created_at, started_at, completed_at
           FROM work_orders
           WHERE assigned_to_sub = $1 AND status NOT IN ('verified', 'rejected')
           ORDER BY
             CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
             due_date ASC NULLS LAST""",
        user.sub,
    )
    return [WorkOrderOut(**dict(r)) for r in rows]


@router.post("/", response_model=WorkOrderOut, status_code=201)
async def create_work_order(
    body: WorkOrderCreate,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO work_orders
           (title, description, order_type, priority, project_id, due_date,
            assigned_by_sub, _modified_by_sub)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
           RETURNING id, title, description, order_type, priority, status,
                     project_id, assigned_to_sub, assigned_by_sub,
                     due_date, created_at, started_at, completed_at""",
        body.title, body.description, body.order_type, body.priority,
        body.project_id, body.due_date, user.sub,
    )
    return WorkOrderOut(**dict(row))


@router.post("/{work_order_id}/assign", response_model=WorkOrderOut)
async def assign_work_order(
    work_order_id: int,
    body: WorkOrderAssign,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """UPDATE work_orders
           SET assigned_to_sub = $1, assigned_by_sub = $2, status = 'assigned',
               _modified_by_sub = $2, _modified_at = NOW()
           WHERE id = $3
           RETURNING id, title, description, order_type, priority, status,
                     project_id, assigned_to_sub, assigned_by_sub,
                     due_date, created_at, started_at, completed_at""",
        body.assigned_to_sub, user.sub, work_order_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Work order not found")
    return WorkOrderOut(**dict(row))


@router.put("/{work_order_id}/status", response_model=WorkOrderOut)
async def change_status(
    work_order_id: int,
    body: WorkOrderStatusChange,
    user: UserInfo = Depends(get_current_user),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    pool = get_pool()
    current = await pool.fetchrow(
        "SELECT status, assigned_to_sub FROM work_orders WHERE id = $1",
        work_order_id,
    )
    if not current:
        raise HTTPException(status_code=404, detail="Work order not found")

    allowed = VALID_TRANSITIONS.get(current["status"], set())
    if body.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current['status']}' to '{body.status}'",
        )

    # Field workers can only change their own assignments
    if not user.is_engineer and current["assigned_to_sub"] != user.sub:
        raise HTTPException(status_code=403, detail="Not assigned to this work order")

    extra_set = ""
    if body.status == "in_progress":
        extra_set = ", started_at = NOW()"
    elif body.status == "completed":
        extra_set = ", completed_at = NOW()"
    elif body.status == "verified":
        extra_set = f", verified_at = NOW(), verified_by_sub = '{user.sub}'"

    row = await pool.fetchrow(
        f"""UPDATE work_orders
            SET status = $1, _modified_by_sub = $2, _modified_at = NOW() {extra_set}
            WHERE id = $3
            RETURNING id, title, description, order_type, priority, status,
                      project_id, assigned_to_sub, assigned_by_sub,
                      due_date, created_at, started_at, completed_at""",
        body.status, user.sub, work_order_id,
    )
    return WorkOrderOut(**dict(row))


# --- Work Order Items --------------------------------------------------------

@router.get("/{work_order_id}/items", response_model=list[WorkOrderItemOut])
async def list_items(
    work_order_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, work_order_id, item_type, description, target_layer,
                  target_fid, quantity, unit, status, completed_at, notes
           FROM work_order_items WHERE work_order_id = $1 ORDER BY id""",
        work_order_id,
    )
    return [WorkOrderItemOut(**dict(r)) for r in rows]


@router.post("/{work_order_id}/items", response_model=WorkOrderItemOut, status_code=201)
async def create_item(
    work_order_id: int,
    body: WorkOrderItemCreate,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO work_order_items
           (work_order_id, item_type, description, target_layer, target_fid, quantity, unit)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           RETURNING id, work_order_id, item_type, description, target_layer,
                     target_fid, quantity, unit, status, completed_at, notes""",
        work_order_id, body.item_type, body.description,
        body.target_layer, body.target_fid, body.quantity, body.unit,
    )
    return WorkOrderItemOut(**dict(row))


@router.put("/{work_order_id}/items/{item_id}/complete")
async def complete_item(
    work_order_id: int,
    item_id: int,
    notes: str = "",
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    await pool.execute(
        """UPDATE work_order_items
           SET status = 'done', completed_at = NOW(), completed_by_sub = $1, notes = $2
           WHERE id = $3 AND work_order_id = $4""",
        user.sub, notes, item_id, work_order_id,
    )
    return {"status": "ok"}


# --- SMR Reports -------------------------------------------------------------

@router.post("/smr-reports", response_model=SMRReportOut, status_code=201)
async def create_smr_report(
    body: SMRReportCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    geom_sql = "NULL"
    params = [
        body.work_order_id, user.sub, body.report_date, body.weather,
        body.crew_size, body.hours_worked,
        json.dumps(body.activities), json.dumps(body.materials_used),
        body.issues, user.sub,
    ]

    if body.latitude is not None and body.longitude is not None:
        geom_sql = f"ST_SetSRID(ST_MakePoint(${len(params) + 1}, ${len(params) + 2}), 4326)"
        params.extend([body.longitude, body.latitude])

    row = await pool.fetchrow(
        f"""INSERT INTO smr_reports
            (work_order_id, reported_by_sub, report_date, weather, crew_size,
             hours_worked, activities, materials_used, issues, _modified_by_sub, geom)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, {geom_sql})
            RETURNING id, work_order_id, reported_by_sub, report_date, weather,
                      crew_size, hours_worked, activities, materials_used, issues""",
        *params,
    )
    return SMRReportOut(**dict(row))


@router.get("/smr-reports", response_model=list[SMRReportOut])
async def list_smr_reports(
    work_order_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, work_order_id, reported_by_sub, report_date, weather,
                  crew_size, hours_worked, activities, materials_used, issues
           FROM smr_reports WHERE work_order_id = $1 ORDER BY report_date DESC""",
        work_order_id,
    )
    return [SMRReportOut(**dict(r)) for r in rows]


# --- Photos ------------------------------------------------------------------

@router.post("/photos/upload")
async def upload_photo(
    related_type: str = Query(...),
    related_id: int = Query(...),
    caption: str = Query(""),
    latitude: float | None = Query(None),
    longitude: float | None = Query(None),
    file: UploadFile = File(...),
    user: UserInfo = Depends(require_any_role),
):
    import os
    import uuid
    from config import settings

    ext = os.path.splitext(file.filename or "photo.jpg")[1]
    filename = f"{related_type}_{related_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(settings.storage_photos_dir, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    pool = get_pool()
    geom_sql = "NULL"
    params = [related_type, related_id, filename, caption, user.sub]
    if latitude is not None and longitude is not None:
        geom_sql = f"ST_SetSRID(ST_MakePoint(${len(params) + 1}, ${len(params) + 2}), 4326)"
        params.extend([longitude, latitude])

    await pool.execute(
        f"""INSERT INTO field_photos (related_type, related_id, photo_path, caption, taken_by_sub, geom)
            VALUES ($1, $2, $3, $4, $5, {geom_sql})""",
        *params,
    )

    return {"status": "ok", "filename": filename}


@router.get("/photos/{photo_id}")
async def get_photo(photo_id: int, user: UserInfo = Depends(get_current_user)):
    import os
    from fastapi.responses import FileResponse
    from config import settings

    pool = get_pool()
    row = await pool.fetchrow("SELECT photo_path FROM field_photos WHERE id = $1", photo_id)
    if not row:
        raise HTTPException(status_code=404, detail="Photo not found")

    filepath = os.path.join(settings.storage_photos_dir, row["photo_path"])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Photo file not found")

    return FileResponse(filepath)

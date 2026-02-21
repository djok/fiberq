from fastapi import APIRouter, Depends, HTTPException

from database import get_pool
from auth.zitadel import get_current_user
from auth.models import UserInfo
from auth.roles import require_engineer_or_admin
from projects.models import ProjectCreate, ProjectUpdate, ProjectOut

router = APIRouter()


@router.get("/", response_model=list[ProjectOut])
async def list_projects(user: UserInfo = Depends(get_current_user)):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, name, description, created_at, created_by_sub FROM projects ORDER BY id"
    )
    return [ProjectOut(**dict(r)) for r in rows]


@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO projects (name, description, created_by_sub, _modified_by_sub)
           VALUES ($1, $2, $3, $3)
           RETURNING id, name, description, created_at, created_by_sub""",
        body.name,
        body.description,
        user.sub,
    )
    return ProjectOut(**dict(row))


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, name, description, created_at, created_by_sub FROM projects WHERE id = $1",
        project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(**dict(row))


@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    existing = await pool.fetchrow("SELECT id FROM projects WHERE id = $1", project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = []
    params = []
    idx = 1

    if body.name is not None:
        updates.append(f"name = ${idx}")
        params.append(body.name)
        idx += 1
    if body.description is not None:
        updates.append(f"description = ${idx}")
        params.append(body.description)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"_modified_by_sub = ${idx}")
    params.append(user.sub)
    idx += 1
    updates.append("_modified_at = NOW()")

    params.append(project_id)
    query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ${idx} RETURNING id, name, description, created_at, created_by_sub"

    row = await pool.fetchrow(query, *params)
    return ProjectOut(**dict(row))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    user: UserInfo = Depends(require_engineer_or_admin),
):
    pool = get_pool()
    result = await pool.execute("DELETE FROM projects WHERE id = $1", project_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Project not found")

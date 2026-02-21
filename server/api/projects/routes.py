import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_pool
from auth.kanidm import get_current_user
from auth.models import UserInfo
from auth.roles import require_project_manager_or_admin
from projects.models import (
    ActivityEntry,
    ActivityPage,
    AssignMemberBody,
    ProjectCreate,
    ProjectDetailOut,
    ProjectMemberOut,
    ProjectOut,
    ProjectStats,
    ProjectUpdate,
    PROJECT_ROLES,
    PROJECT_STATUSES,
)

logger = logging.getLogger("fiberq.projects")

router = APIRouter()

# Infrastructure tables used for PostGIS extent computation
_INFRA_TABLES = [
    "ftth_okna",
    "ftth_stubovi",
    "ftth_kablovi_podzemni",
    "ftth_kablovi_nadzemni",
    "ftth_trase",
    "ftth_cevi",
    "ftth_mufovi",
    "ftth_spojevi",
    "ftth_elements",
]


async def _check_project_manager_permission(project_id: int, user: UserInfo):
    """Check if user is admin, global project_manager, or has manager role in this project.

    Raises 403 if none of these conditions are met.
    """
    if user.is_admin:
        return
    if "project_manager" in user.roles:
        return
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT project_role FROM project_users WHERE project_id = $1 AND user_sub = $2",
        project_id,
        user.sub,
    )
    if not row or row["project_role"] != "manager":
        raise HTTPException(status_code=403, detail="Project manager role required")


def _build_extent_union_query(filter_col: str = "project_id", param_idx: int = 1) -> str:
    """Build UNION ALL query across all infrastructure tables for extent computation."""
    parts = []
    for table in _INFRA_TABLES:
        parts.append(
            f"SELECT {filter_col}, geom FROM {table} WHERE geom IS NOT NULL"
        )
    return " UNION ALL ".join(parts)


# ---------------------------------------------------------------------------
# 1. GET / -- List projects (role-scoped)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ProjectOut])
async def list_projects(user: UserInfo = Depends(get_current_user)):
    pool = get_pool()

    # Admin and project_manager see all projects; others see only assigned
    if user.is_admin or "project_manager" in user.roles:
        rows = await pool.fetch(
            """SELECT p.id, p.name, p.description, p.status,
                      p.created_at, p.created_by_sub,
                      (SELECT COUNT(*) FROM project_users pu WHERE pu.project_id = p.id) as member_count
               FROM projects p
               ORDER BY p.id"""
        )
    else:
        rows = await pool.fetch(
            """SELECT p.id, p.name, p.description, p.status,
                      p.created_at, p.created_by_sub,
                      (SELECT COUNT(*) FROM project_users pu WHERE pu.project_id = p.id) as member_count
               FROM projects p
               JOIN project_users pu ON pu.project_id = p.id
               WHERE pu.user_sub = $1
               ORDER BY p.id""",
            user.sub,
        )

    if not rows:
        return []

    project_ids = [r["id"] for r in rows]

    # Batch-fetch member names
    member_rows = await pool.fetch(
        """SELECT project_id, COALESCE(user_display_name, user_sub) as name
           FROM project_users
           WHERE project_id = ANY($1)""",
        project_ids,
    )
    member_names_map: dict[int, list[str]] = {}
    for mr in member_rows:
        member_names_map.setdefault(mr["project_id"], []).append(mr["name"])

    # Batch-compute extents across all infrastructure tables
    union_query = _build_extent_union_query()
    extent_rows = await pool.fetch(
        f"""SELECT project_id,
                   ST_AsGeoJSON(ST_Envelope(ST_Extent(geom)))::json as extent
            FROM ({union_query}) combined
            WHERE project_id = ANY($1)
            GROUP BY project_id""",
        project_ids,
    )
    extent_map: dict[int, dict] = {r["project_id"]: r["extent"] for r in extent_rows}

    # Fall back to bounds_geom for projects without infrastructure features
    missing_extent_ids = [pid for pid in project_ids if pid not in extent_map]
    if missing_extent_ids:
        bounds_rows = await pool.fetch(
            """SELECT id, ST_AsGeoJSON(bounds_geom)::json as extent
               FROM projects
               WHERE id = ANY($1) AND bounds_geom IS NOT NULL""",
            missing_extent_ids,
        )
        for br in bounds_rows:
            extent_map[br["id"]] = br["extent"]

    return [
        ProjectOut(
            id=r["id"],
            name=r["name"],
            description=r["description"],
            status=r["status"],
            member_count=r["member_count"],
            member_names=member_names_map.get(r["id"], []),
            extent=extent_map.get(r["id"]),
            created_at=r["created_at"],
            created_by_sub=r["created_by_sub"],
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# 2. POST / -- Create project
# ---------------------------------------------------------------------------

@router.post("/", response_model=ProjectOut, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: UserInfo = Depends(require_project_manager_or_admin),
):
    if body.status not in PROJECT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Must be one of: {', '.join(PROJECT_STATUSES)}",
        )

    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO projects (name, description, status, created_by_sub, _modified_by_sub)
           VALUES ($1, $2, $3, $4, $4)
           RETURNING id, name, description, status, created_at, created_by_sub""",
        body.name,
        body.description,
        body.status,
        user.sub,
    )
    return ProjectOut(**dict(row))


# ---------------------------------------------------------------------------
# 3. GET /{project_id}/stats -- Project dashboard statistics
# ---------------------------------------------------------------------------


async def _check_project_visibility(project_id: int, user: UserInfo):
    """Verify project exists and user has visibility.

    Returns the project row on success.
    Raises 404 if project not found, 403 if user lacks access.
    """
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, status FROM projects WHERE id = $1", project_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    if not user.is_admin and "project_manager" not in user.roles:
        assignment = await pool.fetchrow(
            "SELECT 1 FROM project_users WHERE project_id = $1 AND user_sub = $2",
            project_id,
            user.sub,
        )
        if not assignment:
            raise HTTPException(status_code=403, detail="Not assigned to this project")
    return row


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    await _check_project_visibility(project_id, user)
    pool = get_pool()

    # Determine if project has synced data (at least one completed sync_log entry)
    has_sync = await pool.fetchval(
        "SELECT EXISTS(SELECT 1 FROM sync_log WHERE project_id = $1 AND status = 'completed')",
        project_id,
    )

    # Element counts via single UNION ALL query
    counts_row = await pool.fetchrow(
        """SELECT
               SUM(CASE WHEN source = 'mufovi' THEN cnt ELSE 0 END) as closures,
               SUM(CASE WHEN source = 'stubovi' THEN cnt ELSE 0 END) as poles,
               SUM(CASE WHEN source IN ('kp', 'kn') THEN cnt ELSE 0 END) as cables,
               SUM(CASE WHEN source IN ('kp', 'kn') THEN total_len ELSE 0 END) as cable_length_m
           FROM (
               SELECT 'mufovi' as source, COUNT(*) as cnt, 0::real as total_len
                   FROM ftth_mufovi WHERE project_id = $1
               UNION ALL
               SELECT 'stubovi', COUNT(*), 0
                   FROM ftth_stubovi WHERE project_id = $1
               UNION ALL
               SELECT 'kp', COUNT(*), COALESCE(SUM(total_len_m), 0)
                   FROM ftth_kablovi_podzemni WHERE project_id = $1
               UNION ALL
               SELECT 'kn', COUNT(*), COALESCE(SUM(total_len_m), 0)
                   FROM ftth_kablovi_nadzemni WHERE project_id = $1
           ) counts""",
        project_id,
    )

    # Team size
    team_size = await pool.fetchval(
        "SELECT COUNT(*) FROM project_users WHERE project_id = $1",
        project_id,
    )

    # Last completed sync
    sync_row = await pool.fetchrow(
        """SELECT completed_at, features_uploaded
           FROM sync_log
           WHERE project_id = $1 AND status = 'completed'
           ORDER BY completed_at DESC
           LIMIT 1""",
        project_id,
    )

    return ProjectStats(
        closures=int(counts_row["closures"]) if has_sync else None,
        poles=int(counts_row["poles"]) if has_sync else None,
        cables=int(counts_row["cables"]) if has_sync else None,
        cable_length_m=round(float(counts_row["cable_length_m"]), 1) if has_sync else None,
        team_size=team_size,
        last_sync_at=sync_row["completed_at"] if sync_row else None,
        last_sync_features=sync_row["features_uploaded"] if sync_row else None,
    )


# ---------------------------------------------------------------------------
# 4. GET /{project_id}/activity -- Project activity feed
# ---------------------------------------------------------------------------

@router.get("/{project_id}/activity", response_model=ActivityPage)
async def get_project_activity(
    project_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    before: str | None = None,
    user: UserInfo = Depends(get_current_user),
):
    await _check_project_visibility(project_id, user)
    pool = get_pool()

    # Build parameterised cursor clause
    params: list = [project_id]
    before_clause = ""
    if before:
        before_dt = datetime.fromisoformat(before)
        params.append(before_dt)
        before_clause = "AND event_at < $2"

    query = f"""
        SELECT event_type, event_at, user_sub, user_display_name, details
        FROM (
            -- Sync uploads
            SELECT
                'sync_upload' as event_type,
                COALESCE(sl.completed_at, sl.started_at) as event_at,
                sl.user_sub,
                ul.username as user_display_name,
                jsonb_build_object(
                    'features_uploaded', sl.features_uploaded,
                    'sync_type', sl.sync_type
                ) as details
            FROM sync_log sl
            LEFT JOIN user_logins ul ON ul.user_sub = sl.user_sub
            WHERE sl.project_id = $1 AND sl.status = 'completed'

            UNION ALL

            -- Member assignments
            SELECT
                'member_assigned' as event_type,
                pu.assigned_at as event_at,
                pu.assigned_by_sub as user_sub,
                pu.user_display_name,
                jsonb_build_object(
                    'member_name', pu.user_display_name,
                    'project_role', pu.project_role
                ) as details
            FROM project_users pu
            WHERE pu.project_id = $1

            UNION ALL

            -- Status changes and member removals from activity log
            SELECT
                pal.event_type,
                pal.created_at as event_at,
                pal.user_sub,
                ul.username as user_display_name,
                pal.details
            FROM project_activity_log pal
            LEFT JOIN user_logins ul ON ul.user_sub = pal.user_sub
            WHERE pal.project_id = $1
        ) combined
        WHERE TRUE {before_clause}
        ORDER BY event_at DESC
        LIMIT {limit + 1}
    """

    rows = await pool.fetch(query, *params)
    has_more = len(rows) > limit
    entries = [
        ActivityEntry(
            event_type=r["event_type"],
            event_at=r["event_at"],
            user_sub=r["user_sub"],
            user_display_name=r["user_display_name"],
            details=json.loads(r["details"]) if isinstance(r["details"], str) else r["details"],
        )
        for r in rows[:limit]
    ]
    return ActivityPage(entries=entries, has_more=has_more)


# ---------------------------------------------------------------------------
# 5. GET /{project_id} -- Project detail with members and extent
# ---------------------------------------------------------------------------

@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """SELECT id, name, description, status, created_at, created_by_sub
           FROM projects WHERE id = $1""",
        project_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    # Visibility check: non-admin/non-PM must be assigned
    if not user.is_admin and "project_manager" not in user.roles:
        assignment = await pool.fetchrow(
            "SELECT 1 FROM project_users WHERE project_id = $1 AND user_sub = $2",
            project_id,
            user.sub,
        )
        if not assignment:
            raise HTTPException(status_code=403, detail="Not assigned to this project")

    # Fetch members
    member_rows = await pool.fetch(
        """SELECT id, user_sub, user_display_name, user_email, project_role, assigned_at
           FROM project_users
           WHERE project_id = $1
           ORDER BY assigned_at""",
        project_id,
    )
    members = [ProjectMemberOut(**dict(mr)) for mr in member_rows]

    # Compute extent across all infrastructure tables for this project
    union_query = _build_extent_union_query()
    extent_row = await pool.fetchrow(
        f"""SELECT ST_AsGeoJSON(ST_Envelope(ST_Extent(geom)))::json as extent
            FROM ({union_query}) combined
            WHERE project_id = $1""",
        project_id,
    )
    extent = extent_row["extent"] if extent_row and extent_row["extent"] else None

    # Fall back to project bounds_geom
    if not extent:
        bounds_row = await pool.fetchrow(
            "SELECT ST_AsGeoJSON(bounds_geom)::json as extent FROM projects WHERE id = $1",
            project_id,
        )
        if bounds_row and bounds_row["extent"]:
            extent = bounds_row["extent"]

    return ProjectDetailOut(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        status=row["status"],
        created_at=row["created_at"],
        created_by_sub=row["created_by_sub"],
        members=members,
        extent=extent,
    )


# ---------------------------------------------------------------------------
# 6. PUT /{project_id} -- Update project
# ---------------------------------------------------------------------------

@router.put("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    existing = await pool.fetchrow(
        "SELECT id, status FROM projects WHERE id = $1", project_id
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    # Permission: admin, global PM, or project-level manager
    await _check_project_manager_permission(project_id, user)

    old_status = existing["status"]

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
    if body.status is not None:
        if body.status not in PROJECT_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{body.status}'. Must be one of: {', '.join(PROJECT_STATUSES)}",
            )
        updates.append(f"status = ${idx}")
        params.append(body.status)
        idx += 1

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append(f"_modified_by_sub = ${idx}")
    params.append(user.sub)
    idx += 1
    updates.append("_modified_at = NOW()")

    params.append(project_id)
    query = (
        f"UPDATE projects SET {', '.join(updates)} "
        f"WHERE id = ${idx} "
        f"RETURNING id, name, description, status, created_at, created_by_sub"
    )

    row = await pool.fetchrow(query, *params)

    # Log status change to activity log
    if body.status is not None and body.status != old_status:
        await pool.execute(
            """INSERT INTO project_activity_log (project_id, event_type, user_sub, details)
               VALUES ($1, 'status_change', $2, $3)""",
            project_id,
            user.sub,
            json.dumps({"old_status": old_status, "new_status": body.status}),
        )
        logger.info(
            "Project %d status changed from %s to %s by %s",
            project_id, old_status, body.status, user.sub,
        )

    return ProjectOut(**dict(row))


# ---------------------------------------------------------------------------
# 7. DELETE /{project_id} -- Delete project
# ---------------------------------------------------------------------------

@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    user: UserInfo = Depends(require_project_manager_or_admin),
):
    pool = get_pool()
    result = await pool.execute("DELETE FROM projects WHERE id = $1", project_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Project not found")


# ---------------------------------------------------------------------------
# 8. POST /{project_id}/members -- Assign member to project
# ---------------------------------------------------------------------------

@router.post("/{project_id}/members", response_model=ProjectMemberOut, status_code=201)
async def assign_member(
    project_id: int,
    body: AssignMemberBody,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()

    # Verify project exists
    project = await pool.fetchrow("SELECT id FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Permission check
    await _check_project_manager_permission(project_id, user)

    # Validate project role
    if body.project_role not in PROJECT_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project role '{body.project_role}'. Must be one of: {', '.join(PROJECT_ROLES)}",
        )

    # Upsert: insert or update on conflict
    row = await pool.fetchrow(
        """INSERT INTO project_users (project_id, user_sub, user_display_name, user_email, project_role, assigned_by_sub)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (project_id, user_sub)
           DO UPDATE SET project_role = EXCLUDED.project_role,
                         user_display_name = EXCLUDED.user_display_name,
                         user_email = EXCLUDED.user_email,
                         assigned_by_sub = EXCLUDED.assigned_by_sub
           RETURNING id, user_sub, user_display_name, user_email, project_role, assigned_at""",
        project_id,
        body.user_sub,
        body.user_display_name,
        body.user_email,
        body.project_role,
        user.sub,
    )
    logger.info(
        "Member %s assigned to project %d with role %s by %s",
        body.user_sub,
        project_id,
        body.project_role,
        user.sub,
    )
    return ProjectMemberOut(**dict(row))


# ---------------------------------------------------------------------------
# 9. DELETE /{project_id}/members/{member_id} -- Remove member
# ---------------------------------------------------------------------------

@router.delete("/{project_id}/members/{member_id}", status_code=204)
async def remove_member(
    project_id: int,
    member_id: int,
    user: UserInfo = Depends(get_current_user),
):
    # Permission check
    await _check_project_manager_permission(project_id, user)

    pool = get_pool()

    # Fetch member info before deletion (needed for activity log)
    member_row = await pool.fetchrow(
        "SELECT user_display_name, project_role FROM project_users WHERE id = $1 AND project_id = $2",
        member_id,
        project_id,
    )
    if not member_row:
        raise HTTPException(status_code=404, detail="Member not found in this project")

    await pool.execute(
        "DELETE FROM project_users WHERE id = $1 AND project_id = $2",
        member_id,
        project_id,
    )

    # Log removal to activity log
    await pool.execute(
        """INSERT INTO project_activity_log (project_id, event_type, user_sub, details)
           VALUES ($1, 'member_removed', $2, $3)""",
        project_id,
        user.sub,
        json.dumps({
            "member_name": member_row["user_display_name"],
            "project_role": member_row["project_role"],
        }),
    )
    logger.info("Member %d removed from project %d by %s", member_id, project_id, user.sub)


# ---------------------------------------------------------------------------
# 10. GET /{project_id}/assignable-users -- List users available for assignment
# ---------------------------------------------------------------------------

@router.get("/{project_id}/assignable-users")
async def list_assignable_users(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    # Permission check
    await _check_project_manager_permission(project_id, user)

    pool = get_pool()
    rows = await pool.fetch(
        """SELECT user_sub, username as display_name, NULL as email
           FROM user_logins
           ORDER BY username"""
    )
    return [
        {
            "user_sub": r["user_sub"],
            "display_name": r["display_name"],
            "email": r["email"],
        }
        for r in rows
    ]

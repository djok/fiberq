from fastapi import APIRouter, Depends, HTTPException

from database import get_pool
from auth.zitadel import get_current_user
from auth.models import UserInfo
from auth.roles import require_any_role
from fiber_plan.models import (
    SpliceClosureCreate, SpliceClosureOut,
    SpliceTrayCreate, SpliceTrayOut,
    SpliceCreate, SpliceOut,
    PatchConnectionCreate, PatchConnectionOut,
    FiberPathOut,
)
from fiber_plan.tracer import trace_fiber_path

router = APIRouter()


# --- Splice Closures --------------------------------------------------------

@router.get("/closures", response_model=list[SpliceClosureOut])
async def list_closures(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, muf_fid, closure_type, closure_model, tray_count, max_splices, project_id
           FROM fiber_splice_closures WHERE project_id = $1 ORDER BY id""",
        project_id,
    )
    return [SpliceClosureOut(**dict(r)) for r in rows]


@router.post("/closures", response_model=SpliceClosureOut, status_code=201)
async def create_closure(
    body: SpliceClosureCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO fiber_splice_closures
           (muf_fid, closure_type, closure_model, tray_count, max_splices, project_id, _modified_by_sub)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           RETURNING id, muf_fid, closure_type, closure_model, tray_count, max_splices, project_id""",
        body.muf_fid, body.closure_type, body.closure_model,
        body.tray_count, body.max_splices, body.project_id, user.sub,
    )
    return SpliceClosureOut(**dict(row))


# --- Splice Trays ------------------------------------------------------------

@router.get("/closures/{closure_id}/trays", response_model=list[SpliceTrayOut])
async def list_trays(closure_id: int, user: UserInfo = Depends(get_current_user)):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, closure_id, tray_number, tray_type, capacity FROM fiber_splice_trays WHERE closure_id = $1 ORDER BY tray_number",
        closure_id,
    )
    return [SpliceTrayOut(**dict(r)) for r in rows]


@router.post("/closures/{closure_id}/trays", response_model=SpliceTrayOut, status_code=201)
async def create_tray(
    closure_id: int,
    body: SpliceTrayCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO fiber_splice_trays (closure_id, tray_number, tray_type, capacity)
           VALUES ($1, $2, $3, $4)
           RETURNING id, closure_id, tray_number, tray_type, capacity""",
        closure_id, body.tray_number, body.tray_type, body.capacity,
    )
    return SpliceTrayOut(**dict(row))


# --- Splices -----------------------------------------------------------------

@router.get("/splices", response_model=list[SpliceOut])
async def list_splices(
    tray_id: int | None = None,
    closure_id: int | None = None,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    if tray_id:
        rows = await pool.fetch(
            """SELECT * FROM fiber_splices WHERE tray_id = $1 ORDER BY position_in_tray""",
            tray_id,
        )
    elif closure_id:
        rows = await pool.fetch(
            """SELECT s.* FROM fiber_splices s
               JOIN fiber_splice_trays t ON s.tray_id = t.id
               WHERE t.closure_id = $1
               ORDER BY t.tray_number, s.position_in_tray""",
            closure_id,
        )
    else:
        raise HTTPException(status_code=400, detail="Provide tray_id or closure_id")

    return [SpliceOut(**dict(r)) for r in rows]


@router.post("/splices", response_model=SpliceOut, status_code=201)
async def create_splice(
    body: SpliceCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO fiber_splices
           (tray_id, position_in_tray,
            cable_a_layer_id, cable_a_fid, fiber_a_number, fiber_a_color, tube_a_number, tube_a_color,
            cable_b_layer_id, cable_b_fid, fiber_b_number, fiber_b_color, tube_b_number, tube_b_color,
            splice_type, loss_db, status, notes, _modified_by_sub)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
           RETURNING *""",
        body.tray_id, body.position_in_tray,
        body.cable_a_layer_id, body.cable_a_fid, body.fiber_a_number, body.fiber_a_color,
        body.tube_a_number, body.tube_a_color,
        body.cable_b_layer_id, body.cable_b_fid, body.fiber_b_number, body.fiber_b_color,
        body.tube_b_number, body.tube_b_color,
        body.splice_type, body.loss_db, body.status, body.notes, user.sub,
    )
    return SpliceOut(**dict(row))


@router.put("/splices/{splice_id}", response_model=SpliceOut)
async def update_splice(
    splice_id: int,
    body: SpliceCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """UPDATE fiber_splices SET
            tray_id=$1, position_in_tray=$2,
            cable_a_layer_id=$3, cable_a_fid=$4, fiber_a_number=$5, fiber_a_color=$6,
            tube_a_number=$7, tube_a_color=$8,
            cable_b_layer_id=$9, cable_b_fid=$10, fiber_b_number=$11, fiber_b_color=$12,
            tube_b_number=$13, tube_b_color=$14,
            splice_type=$15, loss_db=$16, status=$17, notes=$18,
            _modified_by_sub=$19, _modified_at=NOW()
           WHERE id=$20 RETURNING *""",
        body.tray_id, body.position_in_tray,
        body.cable_a_layer_id, body.cable_a_fid, body.fiber_a_number, body.fiber_a_color,
        body.tube_a_number, body.tube_a_color,
        body.cable_b_layer_id, body.cable_b_fid, body.fiber_b_number, body.fiber_b_color,
        body.tube_b_number, body.tube_b_color,
        body.splice_type, body.loss_db, body.status, body.notes,
        user.sub, splice_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Splice not found")
    return SpliceOut(**dict(row))


# --- Patch Connections -------------------------------------------------------

@router.get("/patches", response_model=list[PatchConnectionOut])
async def list_patches(
    element_fid: int,
    element_layer_id: str,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, element_layer_id, element_fid, port_number,
                  fiber_cable_layer_id, fiber_cable_fid, fiber_number,
                  fiber_color, connector_type, status
           FROM fiber_patch_connections
           WHERE element_fid = $1 AND element_layer_id = $2
           ORDER BY port_number""",
        element_fid, element_layer_id,
    )
    return [PatchConnectionOut(**dict(r)) for r in rows]


@router.post("/patches", response_model=PatchConnectionOut, status_code=201)
async def create_patch(
    body: PatchConnectionCreate,
    user: UserInfo = Depends(require_any_role),
):
    pool = get_pool()
    row = await pool.fetchrow(
        """INSERT INTO fiber_patch_connections
           (element_layer_id, element_fid, port_number,
            fiber_cable_layer_id, fiber_cable_fid, fiber_number,
            fiber_color, connector_type, status, _modified_by_sub)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
           RETURNING id, element_layer_id, element_fid, port_number,
                     fiber_cable_layer_id, fiber_cable_fid, fiber_number,
                     fiber_color, connector_type, status""",
        body.element_layer_id, body.element_fid, body.port_number,
        body.fiber_cable_layer_id, body.fiber_cable_fid, body.fiber_number,
        body.fiber_color, body.connector_type, body.status, user.sub,
    )
    return PatchConnectionOut(**dict(row))


# --- Fiber Path Tracing ------------------------------------------------------

@router.get("/trace/{element_fid}/{port_number}", response_model=FiberPathOut | None)
async def trace_fiber(
    element_fid: int,
    port_number: int,
    element_layer_id: str = "",
    user: UserInfo = Depends(get_current_user),
):
    """Trace a fiber end-to-end from an element port through splices to the other end."""
    pool = get_pool()
    path = await trace_fiber_path(pool, element_fid, port_number, element_layer_id)
    if not path:
        raise HTTPException(status_code=404, detail="No fiber path found from this port")
    return path


@router.get("/paths", response_model=list[FiberPathOut])
async def list_paths(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, path_name, olt_element_fid, olt_port_number,
                  onu_element_fid, onu_port_number,
                  total_loss_db, total_length_m, status, path_segments
           FROM fiber_paths WHERE project_id = $1 ORDER BY id""",
        project_id,
    )
    return [FiberPathOut(**dict(r)) for r in rows]

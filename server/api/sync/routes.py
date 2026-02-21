import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse

from config import settings
from database import get_pool
from auth.kanidm import get_current_user
from auth.models import UserInfo
from sync.merger import merge_gpkg_to_postgis
from sync.exporter import export_postgis_to_gpkg

logger = logging.getLogger("fiberq.sync")

router = APIRouter()


@router.post("/upload")
async def upload_gpkg(
    project_id: int = Query(..., description="Project ID"),
    file: UploadFile = File(...),
    user: UserInfo = Depends(get_current_user),
):
    """Upload a GeoPackage from QField and merge changes into PostGIS."""
    if not file.filename or not file.filename.endswith(".gpkg"):
        raise HTTPException(status_code=400, detail="File must be a .gpkg GeoPackage")

    pool = get_pool()

    # Log sync start
    sync_row = await pool.fetchrow(
        """INSERT INTO sync_log (user_sub, project_id, sync_type)
           VALUES ($1, $2, 'upload')
           RETURNING id""",
        user.sub,
        project_id,
    )
    sync_id = sync_row["id"]

    # Save uploaded GPKG
    upload_dir = os.path.join(settings.storage_gpkg_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{user.sub}_{project_id}_{uuid.uuid4().hex[:8]}.gpkg"
    filepath = os.path.join(upload_dir, filename)

    try:
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)

        result = await merge_gpkg_to_postgis(filepath, project_id, user.sub, pool)

        await pool.execute(
            """UPDATE sync_log
               SET completed_at = NOW(), status = 'completed',
                   features_uploaded = $1, conflicts_resolved = $2,
                   details = $3::jsonb
               WHERE id = $4""",
            result["features_merged"],
            result["conflicts"],
            '{}',
            sync_id,
        )

        return {
            "status": "ok",
            "sync_id": sync_id,
            "features_merged": result["features_merged"],
            "conflicts": result["conflicts"],
        }

    except Exception as e:
        logger.exception("Sync upload failed")
        await pool.execute(
            "UPDATE sync_log SET completed_at = NOW(), status = 'failed' WHERE id = $1",
            sync_id,
        )
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@router.get("/download/{project_id}")
async def download_gpkg(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    """Export current PostGIS data as GeoPackage for QField."""
    pool = get_pool()

    project = await pool.fetchrow("SELECT id FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    download_dir = os.path.join(settings.storage_gpkg_dir, "downloads")
    os.makedirs(download_dir, exist_ok=True)
    filename = f"fiberq_{project_id}_{uuid.uuid4().hex[:8]}.gpkg"
    filepath = os.path.join(download_dir, filename)

    try:
        await export_postgis_to_gpkg(filepath, project_id, pool)

        # Log sync
        await pool.execute(
            """INSERT INTO sync_log (user_sub, project_id, sync_type, completed_at, status)
               VALUES ($1, $2, 'download', NOW(), 'completed')""",
            user.sub,
            project_id,
        )

        return FileResponse(
            filepath,
            media_type="application/geopackage+sqlite3",
            filename=f"fiberq_project_{project_id}.gpkg",
        )

    except Exception as e:
        logger.exception("GPKG export failed")
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.get("/status")
async def sync_status(
    project_id: int = Query(...),
    user: UserInfo = Depends(get_current_user),
):
    """Get recent sync history for a project."""
    pool = get_pool()
    rows = await pool.fetch(
        """SELECT id, user_sub, sync_type, started_at, completed_at,
                  features_uploaded, features_downloaded, conflicts_resolved, status
           FROM sync_log
           WHERE project_id = $1
           ORDER BY started_at DESC
           LIMIT 20""",
        project_id,
    )
    return [dict(r) for r in rows]

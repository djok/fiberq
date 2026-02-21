"""Merge a GeoPackage (from QField) into PostGIS.

Strategy: timestamp-based feature-level merge.
- For each feature in the GPKG, compare _modified_at with PostGIS.
- If GPKG is newer, update PostGIS.
- If PostGIS is newer, skip (conflict logged).
- New features (no matching id) are inserted.
"""
import logging

import asyncpg
import fiona
from shapely.geometry import shape, mapping
from shapely import wkb

logger = logging.getLogger("fiberq.sync.merger")

# Mapping of GPKG layer names to PostGIS tables
LAYER_TABLE_MAP = {
    "OKNA": "ftth_okna",
    "Stubovi": "ftth_stubovi",
    "Kablovi_podzemni": "ftth_kablovi_podzemni",
    "Kablovi_vazdusni": "ftth_kablovi_nadzemni",
    "Trasa": "ftth_trase",
    "PE cevi": "ftth_cevi",
    "Nastavci": "ftth_mufovi",
    "Prekid vlakna": "ftth_spojevi",
    "Opticke_rezerve": "ftth_spojevi",
    "fiber_splices": "fiber_splices",
    "smr_reports": "smr_reports",
    "work_order_items": "work_order_items",
}


async def merge_gpkg_to_postgis(
    gpkg_path: str,
    project_id: int,
    user_sub: str,
    pool: asyncpg.Pool,
) -> dict:
    """Merge GPKG data into PostGIS. Returns merge statistics."""
    stats = {"features_merged": 0, "conflicts": 0, "errors": 0}

    try:
        layers = fiona.listlayers(gpkg_path)
    except Exception as e:
        logger.error("Cannot read GPKG layers: %s", e)
        return stats

    async with pool.acquire() as conn:
        async with conn.transaction():
            for layer_name in layers:
                table = LAYER_TABLE_MAP.get(layer_name)
                if not table:
                    logger.debug("Skipping unmapped layer: %s", layer_name)
                    continue

                try:
                    result = await _merge_layer(
                        conn, gpkg_path, layer_name, table, project_id, user_sub
                    )
                    stats["features_merged"] += result["merged"]
                    stats["conflicts"] += result["conflicts"]
                except Exception as e:
                    logger.error("Error merging layer %s: %s", layer_name, e)
                    stats["errors"] += 1

    return stats


async def _merge_layer(
    conn: asyncpg.Connection,
    gpkg_path: str,
    layer_name: str,
    table: str,
    project_id: int,
    user_sub: str,
) -> dict:
    """Merge a single GPKG layer into a PostGIS table."""
    result = {"merged": 0, "conflicts": 0}

    with fiona.open(gpkg_path, layer=layer_name) as src:
        for feature in src:
            props = dict(feature.get("properties", {}))
            geom = feature.get("geometry")

            fid = props.pop("id", None)
            props.pop("_modified_by_sub", None)

            if geom:
                geom_wkt = shape(geom).wkt
            else:
                geom_wkt = None

            if fid:
                # Check if feature exists in PostGIS
                existing = await conn.fetchrow(
                    f"SELECT id, _modified_at FROM {table} WHERE id = $1",
                    fid,
                )

                if existing:
                    gpkg_modified = props.get("_modified_at")
                    pg_modified = existing["_modified_at"]

                    if gpkg_modified and pg_modified and gpkg_modified <= pg_modified:
                        result["conflicts"] += 1
                        continue

                    # Update existing feature
                    set_clauses = []
                    params = []
                    idx = 1
                    for key, val in props.items():
                        if key.startswith("_") and key != "_modified_at":
                            continue
                        set_clauses.append(f"{key} = ${idx}")
                        params.append(val)
                        idx += 1

                    set_clauses.append(f"_modified_by_sub = ${idx}")
                    params.append(user_sub)
                    idx += 1
                    set_clauses.append("_modified_at = NOW()")

                    if geom_wkt:
                        set_clauses.append(f"geom = ST_GeomFromText(${idx}, 4326)")
                        params.append(geom_wkt)
                        idx += 1

                    params.append(fid)
                    query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ${idx}"

                    try:
                        await conn.execute(query, *params)
                        result["merged"] += 1
                    except Exception as e:
                        logger.warning("Failed to update %s id=%s: %s", table, fid, e)
                else:
                    # Insert with specific ID
                    await _insert_feature(conn, table, props, geom_wkt, project_id, user_sub, fid)
                    result["merged"] += 1
            else:
                # New feature without ID
                await _insert_feature(conn, table, props, geom_wkt, project_id, user_sub)
                result["merged"] += 1

    return result


async def _insert_feature(
    conn: asyncpg.Connection,
    table: str,
    props: dict,
    geom_wkt: str | None,
    project_id: int,
    user_sub: str,
    fid: int | None = None,
):
    """Insert a new feature into PostGIS."""
    columns = []
    placeholders = []
    values = []
    idx = 1

    if fid:
        columns.append("id")
        placeholders.append(f"${idx}")
        values.append(fid)
        idx += 1

    for key, val in props.items():
        if key.startswith("_"):
            continue
        columns.append(key)
        placeholders.append(f"${idx}")
        values.append(val)
        idx += 1

    columns.append("project_id")
    placeholders.append(f"${idx}")
    values.append(project_id)
    idx += 1

    columns.append("_modified_by_sub")
    placeholders.append(f"${idx}")
    values.append(user_sub)
    idx += 1

    columns.append("_modified_at")
    placeholders.append("NOW()")

    if geom_wkt:
        columns.append("geom")
        placeholders.append(f"ST_GeomFromText(${idx}, 4326)")
        values.append(geom_wkt)
        idx += 1

    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

    try:
        await conn.execute(query, *values)
    except Exception as e:
        logger.warning("Failed to insert into %s: %s", table, e)

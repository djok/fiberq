"""Export PostGIS data to GeoPackage for QField download."""
import logging
import os

import asyncpg
import fiona
from fiona.crs import from_epsg
from shapely import wkb

logger = logging.getLogger("fiberq.sync.exporter")

# Tables to export and their geometry types
EXPORT_TABLES = [
    ("ftth_okna", "Point", "OKNA"),
    ("ftth_stubovi", "Point", "Stubovi"),
    ("ftth_kablovi_podzemni", "LineString", "Kablovi_podzemni"),
    ("ftth_kablovi_nadzemni", "LineString", "Kablovi_vazdusni"),
    ("ftth_trase", "LineString", "Trasa"),
    ("ftth_cevi", "LineString", "PE cevi"),
    ("ftth_mufovi", "Point", "Nastavci"),
    ("ftth_spojevi", "Point", "Prekid vlakna"),
    ("ftth_elements", "Point", "Elements"),
    ("fiber_splice_closures", "Point", "Splice_closures"),
    ("work_orders", "Polygon", "Work_orders"),
    ("smr_reports", "Point", "SMR_reports"),
]


async def export_postgis_to_gpkg(
    gpkg_path: str,
    project_id: int,
    pool: asyncpg.Pool,
):
    """Export all project tables from PostGIS to a GeoPackage."""
    if os.path.exists(gpkg_path):
        os.remove(gpkg_path)

    async with pool.acquire() as conn:
        for table, geom_type, layer_name in EXPORT_TABLES:
            try:
                await _export_table(conn, gpkg_path, table, geom_type, layer_name, project_id)
            except Exception as e:
                logger.warning("Failed to export %s: %s", table, e)


async def _export_table(
    conn: asyncpg.Connection,
    gpkg_path: str,
    table: str,
    geom_type: str,
    layer_name: str,
    project_id: int,
):
    """Export a single PostGIS table to a GPKG layer."""
    # Get column info
    columns_info = await conn.fetch(
        """SELECT column_name, data_type
           FROM information_schema.columns
           WHERE table_schema = 'fiberq' AND table_name = $1
           AND column_name != 'geom'
           ORDER BY ordinal_position""",
        table,
    )

    if not columns_info:
        logger.debug("Table %s has no columns, skipping", table)
        return

    col_names = [c["column_name"] for c in columns_info]
    col_select = ", ".join(col_names)

    geom_col = "geom"
    has_geom = await conn.fetchval(
        """SELECT EXISTS(
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'fiberq' AND table_name = $1 AND column_name = 'geom'
        )""",
        table,
    )

    # Build query
    if has_geom:
        query = f"SELECT {col_select}, ST_AsText(geom) as geom_wkt FROM {table} WHERE project_id = $1 OR project_id IS NULL"
    else:
        query = f"SELECT {col_select} FROM {table} WHERE project_id = $1 OR project_id IS NULL"
        geom_type = None

    rows = await conn.fetch(query, project_id)
    if not rows:
        return

    # Build fiona schema
    fiona_properties = {}
    for c in columns_info:
        col_name = c["column_name"]
        dtype = c["data_type"]
        if dtype in ("integer", "smallint", "bigint"):
            fiona_properties[col_name] = "int"
        elif dtype in ("real", "double precision", "numeric"):
            fiona_properties[col_name] = "float"
        else:
            fiona_properties[col_name] = "str"

    schema = {"properties": fiona_properties}
    if geom_type:
        schema["geometry"] = geom_type

    mode = "a" if os.path.exists(gpkg_path) else "w"

    with fiona.open(
        gpkg_path,
        mode,
        driver="GPKG",
        layer=layer_name,
        schema=schema,
        crs=from_epsg(4326) if geom_type else None,
    ) as dst:
        for row in rows:
            props = {}
            for col_name in col_names:
                val = row[col_name]
                if val is not None:
                    props[col_name] = val
                else:
                    props[col_name] = None

            geom = None
            if has_geom and row.get("geom_wkt"):
                from shapely import wkt
                geom_shape = wkt.loads(row["geom_wkt"])
                geom = geom_shape.__geo_interface__

            feature = {"properties": props, "geometry": geom}
            dst.write(feature)

    logger.info("Exported %d features from %s to %s", len(rows), table, layer_name)

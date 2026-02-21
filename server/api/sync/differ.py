"""
GPKG ↔ PostGIS Diff Engine

Compares features in a GeoPackage file against PostGIS data,
identifies changes (inserts, updates, deletes), and applies
them with timestamp-based conflict resolution.

Used by the sync endpoint to merge QField edits back into PostGIS.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import fiona
import geopandas as gpd
from shapely.geometry import shape, mapping

from ..database import get_connection

logger = logging.getLogger(__name__)

# Table mapping: GPKG layer name → PostGIS table
SYNC_TABLES = {
    "Route":              "ftth_trase",
    "Poles":              "ftth_stubovi",
    "Manholes":           "ftth_okna",
    "Underground cables": "ftth_kablovi_podzemni",
    "Aerial cables":      "ftth_kablovi_nadzemni",
    "PE pipes":           "ftth_cevi",
    "Joint Closures":     "ftth_mufovi",
    "Fiber break":        "ftth_spojevi",
    "Elements":           "ftth_elements",
    "Splice Closures":    "fiber_splice_closures",
    "Work Orders":        "work_orders",
    "SMR Reports":        "smr_reports",
    "Field Photos":       "field_photos",
}


class SyncDiffer:
    """Compares GPKG features with PostGIS and produces a change set."""

    def __init__(self, gpkg_path: str, schema: str = "fiberq"):
        self.gpkg_path = gpkg_path
        self.schema = schema

    def list_gpkg_layers(self) -> list[str]:
        """List all layers available in the GPKG file."""
        return fiona.listlayers(self.gpkg_path)

    async def compute_diff(self, conn, layer_name: str,
                           table_name: str, user_sub: str) -> dict:
        """
        Compute differences between GPKG layer and PostGIS table.

        Returns:
            {
                "inserts": [feature_dicts...],
                "updates": [feature_dicts...],
                "conflicts": [{"gpkg": feature, "db": feature, "resolution": "..."}],
                "unchanged": int,
                "layer": layer_name,
                "table": table_name,
            }
        """
        # Read GPKG layer
        try:
            gdf = gpd.read_file(self.gpkg_path, layer=layer_name)
        except Exception as e:
            logger.warning(f"Cannot read GPKG layer '{layer_name}': {e}")
            return {"inserts": [], "updates": [], "conflicts": [],
                    "unchanged": 0, "layer": layer_name, "table": table_name}

        if gdf.empty:
            return {"inserts": [], "updates": [], "conflicts": [],
                    "unchanged": 0, "layer": layer_name, "table": table_name}

        # Get existing features from PostGIS
        db_features = await self._fetch_db_features(conn, table_name)

        inserts = []
        updates = []
        conflicts = []
        unchanged = 0

        for _, row in gdf.iterrows():
            gpkg_id = row.get("id") or row.get("fid")
            gpkg_modified = _parse_timestamp(row.get("_modified_at"))
            feature_data = _row_to_dict(row)

            if gpkg_id is None or gpkg_id not in db_features:
                # New feature – insert
                feature_data["_modified_by_sub"] = user_sub
                feature_data["_modified_at"] = _now_iso()
                inserts.append(feature_data)
            else:
                db_feat = db_features[gpkg_id]
                db_modified = _parse_timestamp(db_feat.get("_modified_at"))

                if gpkg_modified and db_modified and gpkg_modified > db_modified:
                    # GPKG is newer → update
                    feature_data["_modified_by_sub"] = user_sub
                    feature_data["_modified_at"] = _now_iso()
                    updates.append(feature_data)
                elif gpkg_modified and db_modified and gpkg_modified < db_modified:
                    # DB is newer → conflict (DB wins by default)
                    conflicts.append({
                        "gpkg": feature_data,
                        "db": db_feat,
                        "resolution": "db_wins",
                    })
                else:
                    # Same timestamp or no timestamp → check if data changed
                    if _features_differ(feature_data, db_feat):
                        # Data changed but timestamps equal → last-write-wins (GPKG wins)
                        feature_data["_modified_by_sub"] = user_sub
                        feature_data["_modified_at"] = _now_iso()
                        updates.append(feature_data)
                    else:
                        unchanged += 1

        return {
            "inserts": inserts,
            "updates": updates,
            "conflicts": conflicts,
            "unchanged": unchanged,
            "layer": layer_name,
            "table": table_name,
        }

    async def apply_diff(self, conn, diff: dict, project_id: Optional[int] = None):
        """Apply computed diff to PostGIS within a transaction."""
        table = diff["table"]
        applied = {"inserted": 0, "updated": 0, "conflicts_skipped": 0}

        for feat in diff["inserts"]:
            try:
                await self._insert_feature(conn, table, feat, project_id)
                applied["inserted"] += 1
            except Exception as e:
                logger.error(f"Insert failed for {table}: {e}")

        for feat in diff["updates"]:
            try:
                await self._update_feature(conn, table, feat)
                applied["updated"] += 1
            except Exception as e:
                logger.error(f"Update failed for {table}: {e}")

        applied["conflicts_skipped"] = len(diff["conflicts"])

        return applied

    async def full_sync(self, conn, user_sub: str,
                        project_id: Optional[int] = None) -> dict:
        """
        Run full sync: diff all matching layers and apply changes.

        Returns summary of all changes applied.
        """
        gpkg_layers = set(self.list_gpkg_layers())
        summary = {"layers": {}, "total_inserted": 0, "total_updated": 0,
                    "total_conflicts": 0}

        for layer_name, table_name in SYNC_TABLES.items():
            if layer_name not in gpkg_layers:
                continue

            diff = await self.compute_diff(conn, layer_name, table_name, user_sub)
            result = await self.apply_diff(conn, diff, project_id)

            summary["layers"][layer_name] = {
                "inserts": result["inserted"],
                "updates": result["updated"],
                "conflicts": result["conflicts_skipped"],
                "unchanged": diff["unchanged"],
            }
            summary["total_inserted"] += result["inserted"]
            summary["total_updated"] += result["updated"]
            summary["total_conflicts"] += result["conflicts_skipped"]

        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_db_features(self, conn, table_name: str) -> dict:
        """Fetch all features from a PostGIS table, indexed by id."""
        try:
            rows = await conn.fetch(
                f"SELECT * FROM {self.schema}.{table_name}"
            )
            return {row["id"]: dict(row) for row in rows}
        except Exception as e:
            logger.warning(f"Cannot fetch from {table_name}: {e}")
            return {}

    async def _insert_feature(self, conn, table_name: str, feat: dict,
                               project_id: Optional[int] = None):
        """Insert a single feature into PostGIS."""
        # Remove id to let DB assign it
        feat_copy = {k: v for k, v in feat.items()
                     if k not in ("id", "fid", "geometry")}
        if project_id and "_project_id" not in feat_copy:
            feat_copy["_project_id"] = project_id

        geom = feat.get("geometry")
        cols = list(feat_copy.keys())
        vals = list(feat_copy.values())

        if geom:
            cols.append("geom")
            vals.append(geom)

        placeholders = [f"${i+1}" for i in range(len(vals))]

        # WKT geometry needs ST_GeomFromText
        if geom:
            placeholders[-1] = f"ST_GeomFromText(${len(vals)}, 4326)"

        sql = (
            f"INSERT INTO {self.schema}.{table_name} "
            f"({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        )
        await conn.execute(sql, *vals)

    async def _update_feature(self, conn, table_name: str, feat: dict):
        """Update a feature in PostGIS by id."""
        feat_id = feat.get("id") or feat.get("fid")
        if feat_id is None:
            return

        feat_copy = {k: v for k, v in feat.items()
                     if k not in ("id", "fid", "geometry")}
        geom = feat.get("geometry")

        set_clauses = []
        vals = []
        idx = 1

        for k, v in feat_copy.items():
            set_clauses.append(f"{k} = ${idx}")
            vals.append(v)
            idx += 1

        if geom:
            set_clauses.append(f"geom = ST_GeomFromText(${idx}, 4326)")
            vals.append(geom)
            idx += 1

        vals.append(feat_id)
        sql = (
            f"UPDATE {self.schema}.{table_name} "
            f"SET {', '.join(set_clauses)} "
            f"WHERE id = ${idx}"
        )
        await conn.execute(sql, *vals)


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def _parse_timestamp(val) -> Optional[datetime]:
    """Parse a timestamp from various formats."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        # ISO format
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row) -> dict:
    """Convert a GeoDataFrame row to a plain dict with WKT geometry."""
    d = {}
    for k, v in row.items():
        if k == "geometry":
            if v is not None and not v.is_empty:
                d["geometry"] = v.wkt
            continue
        # Convert numpy types to Python native
        try:
            import numpy as np
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = float(v)
            elif isinstance(v, np.bool_):
                v = bool(v)
        except ImportError:
            pass
        d[k] = v
    return d


def _features_differ(feat_a: dict, feat_b: dict) -> bool:
    """Check if two feature dicts have different attribute values."""
    # Compare all non-system fields
    skip = {"id", "fid", "geometry", "geom", "_modified_at", "_modified_by_sub"}
    for key in set(feat_a.keys()) | set(feat_b.keys()):
        if key in skip:
            continue
        va = feat_a.get(key)
        vb = feat_b.get(key)
        # Normalize None vs empty string
        if va == "" and vb is None:
            continue
        if va is None and vb == "":
            continue
        if va != vb:
            return True
    return False

# Coding Conventions

**Analysis Date:** 2026-02-21

## Naming Patterns

**Files:**
- Lowercase with underscores: `config.py`, `api_client.py`, `work_orders.py`
- Route/handler files named `routes.py`
- Model files named `models.py`
- Special utility files prefixed with underscore: `_icon_path()`, `_load_server_config()`
- Main entry point: `main_plugin.py` (QGIS plugin), `main.py` (FastAPI server)

**Functions:**
- Private/utility functions prefixed with single underscore: `_get_lang()`, `_fiberq_is_pro_enabled()`, `_load_server_config()`
- Public functions use snake_case: `get_current_user()`, `list_projects()`, `create_work_order()`
- Async functions prefixed with `async def`: `async def get_pool()`, `async def create_pool()`
- API route handlers follow pattern: `list_*`, `create_*`, `get_*`, `update_*`, `delete_*` (e.g., `list_projects()`, `create_project()`)
- Dependency injection functions: `get_db()`, `get_current_user()`, `require_admin()`, `require_engineer()`

**Variables:**
- snake_case throughout: `user_sub`, `project_id`, `gpkg_path`, `sync_id`
- Private module variables use single underscore: `_pool`, `_jwks_cache`, `_openid_config_cache`
- Configuration values: uppercase for constants like `_FIBERQ_PRO_MASTER_KEY = "FIBERQ-PRO-2025"`
- Environment-based prefixes in variable names: `zitadel_domain`, `database_url`, `api_secret_key`

**Types:**
- Pydantic BaseModel for request/response schemas: `UserInfo`, `ProjectCreate`, `ProjectUpdate`, `ProjectOut`
- Input models use suffixes: `*Create`, `*Update`, `*Assign`, `*StatusChange`
- Output models use suffix: `*Out` (e.g., `ProjectOut`, `WorkOrderOut`, `SMRReportOut`)
- SQLAlchemy/asyncpg types: `asyncpg.Pool`, `asyncpg.Connection`, `list[str]`, `str | None`

## Code Style

**Formatting:**
- No explicit formatter configuration found (not using Black, isort, or Prettier)
- Lines appear to follow Python PEP 8 defaults (soft 120-char limit based on observed code)
- Space-separated imports and code sections
- Blank lines separate logical sections within files (comments with dashes: `# --- SECTION ---`)

**Linting:**
- No `.eslintrc`, `pyproject.toml`, or explicit linting configuration detected
- Standard Python conventions appear to be followed organically

## Import Organization

**Order:**
1. Standard library imports: `import logging`, `import os`, `import json`, `from datetime import date, datetime`
2. Third-party framework imports: `from fastapi import FastAPI, APIRouter, Depends`, `from pydantic import BaseModel`
3. Third-party utilities: `import asyncpg`, `import httpx`, `import fiona`, `import geopandas as gpd`
4. Local/relative imports: `from config import settings`, `from database import get_pool`, `from auth.zitadel import get_current_user`

**Path Aliases:**
- Relative imports use dot notation: `from .database import get_pool`, `from .api_client import FiberQApiClient`
- Absolute imports within package: `from config import settings` (FastAPI routes assume api/ is on Python path)
- QGIS plugin addons import from same level: `from .zitadel_auth import get_auth`, `from .api_client import FiberQApiClient`

Example from `server/api/main.py`:
```python
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_pool, close_pool
```

## Error Handling

**Patterns:**
- **FastAPI routes:** Use `HTTPException` with status codes:
  ```python
  if not row:
      raise HTTPException(status_code=404, detail="Project not found")
  if not {"admin", "engineer"}.intersection(user.roles):
      raise HTTPException(status_code=403, detail="Engineer or admin role required")
  ```

- **Sync/merge operations:** Log exceptions with `logger.exception()` and continue or return error stats:
  ```python
  except Exception as e:
      logger.exception("Sync upload failed")
      await pool.execute("UPDATE sync_log SET status = 'failed' WHERE id = $1", sync_id)
  ```

- **Utilities/QGIS plugin:** Raise `RuntimeError` for configuration/auth issues:
  ```python
  if not token:
      raise RuntimeError("Not authenticated. Please sign in first (FiberQ → Sign In).")
  ```

- **Validation:** Check conditions and raise early:
  ```python
  if not file.filename or not file.filename.endswith(".gpkg"):
      raise HTTPException(status_code=400, detail="File must be a .gpkg GeoPackage")
  ```

- **Generic exception handling:** Log with full context (`logger.error()`, `logger.warning()`) for informational recovery

## Logging

**Framework:** Python standard `logging` module

**Patterns:**
- Each module has module-level logger: `logger = logging.getLogger(__name__)` or `logger = logging.getLogger("fiberq.auth")`
- Loggers use hierarchical naming: `"fiberq"`, `"fiberq.auth"`, `"fiberq.sync"`, `"fiberq.sync.exporter"`, `"fiberq.sync.merger"`
- FastAPI startup/shutdown logged in `lifespan()` context manager
- Database operations logged at info/debug level
- Exceptions logged with `logger.exception()` to capture full traceback
- Warnings for non-fatal issues: `logger.warning("Cannot read GPKG layer '%s': %s", layer_name, e)`

Example from `server/api/main.py`:
```python
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger.info("Starting FiberQ API server")
```

## Comments

**When to Comment:**
- Module-level docstrings explaining purpose: Used in sync modules (`differ.py`, `merger.py`, `exporter.py`)
- Section dividers for major code sections: `# --- Register routers -------`, `# --- ICON LOADER (auto-added) ---`
- Inline comments for non-obvious logic (sparse in observed code)
- Unused/commented code not preserved (no commented-out code blocks observed)

**JSDoc/TSDoc:**
- Python uses docstrings (triple-quoted) for functions and classes
- Format: Short description, optional extended explanation, return type hint examples
- Example from `sync/merger.py`:
  ```python
  async def merge_gpkg_to_postgis(
      gpkg_path: str,
      project_id: int,
      user_sub: str,
      pool: asyncpg.Pool,
  ) -> dict:
      """Merge GPKG data into PostGIS. Returns merge statistics."""
  ```

## Function Design

**Size:** Functions range from 10-40 lines (typical); complex async operations (merger, exporter) reach 100-200 lines due to SQL queries and data transformation

**Parameters:**
- Use type hints consistently: `gpkg_path: str`, `project_id: int`, `pool: asyncpg.Pool`
- Optional parameters use union syntax: `token: str | None = None`, `description: str = ""`
- Dependency injection via FastAPI `Depends()`: `user: UserInfo = Depends(get_current_user)`
- Pass related data as objects (Pydantic models): `body: ProjectCreate` not separate name, description params

**Return Values:**
- Async database operations return fetched rows as dicts: `dict(row)` from asyncpg
- Route handlers return Pydantic models or dict literals: `return {"status": "ok", "sync_id": sync_id}`
- Service functions return dict with stats: `return {"features_merged": 0, "conflicts": 0, "errors": 0}`
- Async context managers yield connection: `async with pool.acquire() as conn: yield conn`

## Module Design

**Exports:**
- Explicit imports via named functions: `from .zitadel_auth import get_auth`
- Router registration: `from auth.routes import router as auth_router`
- Config singleton: `settings = Settings()` in `config.py`, imported everywhere

**Barrel Files:**
- `__init__.py` files exist but typically empty or minimal
- Example: `fiberq/addons/__init__.py` has single line: empty or minimal
- Addons load dynamically from method calls, not through `__all__`

## Async Patterns

**Used consistently in:**
- FastAPI route handlers: `async def list_projects(...)`
- Database operations: `async def create_pool()`, `async with pool.acquire() as conn`
- HTTP clients (Zitadel auth): `async with httpx.AsyncClient() as client: resp = await client.get(...)`

**Context managers:**
- Database transactions: `async with pool.acquire() as conn: async with conn.transaction(): yield conn`
- GPKG/file operations: `with fiona.open(gpkg_path, layer=layer_name) as src: ...`

---

*Convention analysis: 2026-02-21*

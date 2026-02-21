# Architecture

**Analysis Date:** 2026-02-21

## Pattern Overview

**Overall:** Distributed Client-Server with Async Data Synchronization

FiberQ is a two-part system:
1. **QGIS Plugin Client** (`/home/rosen/fiberq/fiberq/`) - Desktop GIS application with modular addons
2. **FastAPI Server** (`/home/rosen/fiberq/server/api/`) - REST API with PostgreSQL backend

**Key Characteristics:**
- **Async-first backend:** FastAPI with asyncpg connection pooling for database I/O
- **Modular addon architecture:** Client features loaded as independent addons with minimal coupling
- **Timestamp-based synchronization:** QField GeoPackage merging via feature-level conflict detection
- **OIDC authentication:** Zitadel-based identity with role-based access control (RBAC)
- **GIS-native:** Heavy reliance on PostGIS for spatial queries, QGIS for UI/mapping

## Layers

**Presentation Layer (QGIS Plugin):**
- Purpose: User interface for fiber optic network management in QGIS desktop environment
- Location: `/home/rosen/fiberq/fiberq/`
- Contains: Main plugin entry point, addon dialogs (QDialog subclasses), map tools (QgsMapTool subclasses)
- Depends on: QGIS/Qt libraries, FiberQApiClient, local authentication
- Used by: QGIS application directly
- Key file: `main_plugin.py` (12,991 lines - monolithic UI controller)

**Client API Layer (QGIS Plugin):**
- Purpose: HTTP abstraction for plugin-to-server communication
- Location: `/home/rosen/fiberq/fiberq/addons/api_client.py`
- Contains: `FiberQApiClient` class using stdlib urllib (no external HTTP deps)
- Depends on: configparser, urllib, ssl
- Used by: All addons that need server communication (fiber_plan, work_orders, sync, etc.)
- Error handling: Raises `RuntimeError` on HTTP failures

**Server Application Layer (FastAPI):**
- Purpose: REST API orchestration, request routing, cross-cutting concerns
- Location: `/home/rosen/fiberq/server/api/main.py`
- Contains: FastAPI app instance, middleware setup (CORS), lifespan context manager
- Depends on: FastAPI, database pool, routers
- Used by: ASGI server runtime (e.g., Uvicorn)

**Router/Handler Layer:**
- Purpose: Route-specific business logic and HTTP responses
- Location: `/home/rosen/fiberq/server/api/{auth|projects|sync|fiber_plan|work_orders}/routes.py`
- Contains: APIRouter definitions with decorated endpoint handlers
- Depends on: Models, database, auth dependencies, domain services
- Used by: Main app via `.include_router()`
- Key routers:
  - `auth/routes.py` - Token validation, role queries
  - `projects/routes.py` - Project CRUD
  - `sync/routes.py` - GeoPackage upload/download
  - `fiber_plan/routes.py` - Splice closure management
  - `work_orders/routes.py` - Work order CRUD and SMR reports

**Service/Domain Layer:**
- Purpose: Core business logic for data transformations
- Location: `/home/rosen/fiberq/server/api/sync/{merger|exporter|differ}.py`, `/home/rosen/fiberq/server/api/fiber_plan/tracer.py`
- Contains: Stateless functions for complex operations
- Examples:
  - `sync/merger.py`: Feature-level GPKG→PostGIS merge with timestamp conflict detection
  - `sync/exporter.py`: PostGIS→GPKG export with layer mapping
  - `sync/differ.py`: Change detection for sync protocol
  - `fiber_plan/tracer.py`: Spatial fiber path tracing via PostGIS queries
- Error handling: Logs errors, returns partial results where possible

**Data Access Layer:**
- Purpose: Raw database connectivity and connection management
- Location: `/home/rosen/fiberq/server/api/database.py`
- Contains: Async connection pool management using asyncpg
- Depends on: asyncpg, config
- Used by: Every route/service via `get_pool()` dependency
- Pattern: Global `_pool` singleton with context managers for transactions

**Authentication Layer:**
- Purpose: OIDC token validation and user identity extraction
- Location: `/home/rosen/fiberq/server/api/auth/zitadel.py`
- Contains: Zitadel OpenID Connect integration with JWT validation
- Client-side: `/home/rosen/fiberq/fiberq/addons/zitadel_auth.py`
- Depends on: httpx (server), QGIS Qt (client)
- Caching: OpenID config and JWKS cached globally to minimize external calls

**Models/Schemas Layer:**
- Purpose: Data structure definitions for validation and serialization
- Location: `/home/rosen/fiberq/server/api/{auth|projects|fiber_plan|work_orders}/models.py`
- Contains: Pydantic BaseModel classes for request/response validation
- Pattern: Separate Create/Update/Out models (e.g., `ProjectCreate`, `ProjectUpdate`, `ProjectOut`)
- Used by: Route handlers via type hints and response_model

**Configuration Layer:**
- Purpose: Environment-based settings management
- Location: `/home/rosen/fiberq/server/api/config.py`
- Contains: Pydantic `Settings` class with .env file loading
- Key configs:
  - Database: `database_url`, `database_sync_url`, `db_schema`
  - Auth: `zitadel_domain`, `zitadel_client_id`, `zitadel_project_id`
  - Storage: `storage_photos_dir`, `storage_gpkg_dir`
  - Logging: `log_level`

## Data Flow

**GeoPackage Sync (Upload from QField):**

1. User selects .gpkg file in QGIS plugin UI (via addon dialog)
2. Plugin calls `FiberQApiClient.upload_gpkg(project_id, file, token)`
3. Server route `/sync/upload` receives multipart file
4. Route handler saves file to `storage_gpkg_dir/uploads/` with unique name
5. Calls `sync/merger.merge_gpkg_to_postgis(filepath, project_id, user_sub, pool)`
6. Merger reads each layer from GPKG (layer→table mapping in `LAYER_TABLE_MAP`)
7. For each feature:
   - Reads feature from GPKG with `_modified_at` timestamp
   - Queries PostGIS table for existing feature (by id)
   - If PostGIS feature is older: UPDATE PostGIS feature
   - If PostGIS feature is newer: Log conflict, skip
   - If new feature: INSERT into PostGIS
8. Returns merge statistics (features_merged, conflicts)
9. Route updates `sync_log` table with completion status
10. Client receives confirmation with sync results

**GeoPackage Export (Download to QField):**

1. User requests sync download in QField
2. Plugin calls `FiberQApiClient.download_gpkg(project_id, ...)`
3. Server route `/sync/download` receives request
4. Route calls `sync/exporter.export_postgis_to_gpkg(project_id, pool)`
5. Exporter queries each PostGIS table (reverse table→layer mapping)
6. Creates new GPKG with fiona, writes features with geometries
7. Server returns GPKG file as binary response
8. Client saves to device, QField opens for field editing

**Fiber Path Tracing:**

1. User initiates trace from upstream fiber in splice closure dialog
2. Plugin calls `FiberQApiClient.trace_fiber_path(from_splice_id, to_splice_id, ...)`
3. Server route `/fiber-plan/trace` receives request
4. Route calls `fiber_plan/tracer.trace_fiber_path(from_id, to_id, pool)`
5. Tracer executes recursive PostGIS query:
   - Find fiber connected to from_splice_id
   - Follow path through fiber segments (ftth_spojevi table)
   - Stop at to_splice_id
   - Collect all segment geometries and attributes
6. Returns list of path segments with full geometry
7. Route maps to `FiberPathOut` response model
8. Client visualizes path on map with highlighting

**State Management:**

- **Server-side state:** Minimal - stateless route handlers
  - Connection pool is singleton managed by lifespan context
  - Auth tokens validated per-request via bearer token header
  - OIDC config cached globally (updated on demand)
- **Client-side state:** Plugin settings persisted in `QSettings`
  - Language preference (`FiberQ/lang`)
  - Pro license status (`FiberQ/pro_enabled`)
  - Authentication tokens stored in secure storage via `zitadel_auth.py`
- **Database state:** Source of truth for all business data
  - Features have `_modified_at` and `_modified_by_sub` audit columns
  - Sync operations logged to `sync_log` table for audit trail

## Key Abstractions

**FiberQApiClient:**
- Purpose: HTTP abstraction encapsulating server communication details
- Location: `/home/rosen/fiberq/fiberq/addons/api_client.py`
- Pattern: Stateless client with bearer token support
- Methods: `get()`, `post()`, `put()`, `delete()`, `upload_file()`, `download_file()`
- Error handling: Raises `RuntimeError` with HTTP status and response body on failure

**Feature/Splice:**
- Purpose: Core domain entity representing fiber optic infrastructure
- Examples: Splice closures, individual splices, fiber segments, poles (Stubovi), ducts
- Pattern: PostGIS geometries + QGIS QgsFeature wrapper
- Attributes: id, geometry, properties dict, _modified_at (timestamp), _modified_by_sub (user)

**GeoPackage Layer Mapping:**
- Purpose: Bridge semantic layer names (QField-friendly) to database tables
- Location: `sync/merger.py` `LAYER_TABLE_MAP` dict
- Examples:
  - "OKNA" (optical access points) → `ftth_okna`
  - "Stubovi" (poles) → `ftth_stubovi`
  - "Kablovi_podzemni" (underground cables) → `ftth_kablovi_podzemni`
  - "fiber_splices" → `fiber_splices` (fiber management)
  - "work_order_items" → `work_order_items`

**Addon:**
- Purpose: Pluggable feature module with isolated UI and logic
- Pattern: Class inheriting QDialog or QgsMapTool, loads UI elements on instantiation
- Examples: `fiber_plan.py` (splice management), `work_orders.py` (job tracking), `publish_pg.py` (data publishing)
- Activation: Main plugin instantiates addons conditionally via toolbar buttons/menu items

**User Context (UserInfo):**
- Purpose: Authentication identity with role-based permissions
- Location: `auth/models.py`
- Fields: `sub` (unique ID), `email`, `name`, `roles` (list of role strings)
- Properties: `is_admin`, `is_engineer`, `is_field_worker` (hierarchical role checks)
- Validation: JWT token from Zitadel OIDC provider

## Entry Points

**Server:**
- Location: `/home/rosen/fiberq/server/api/main.py`
- Triggers: ASGI server startup (e.g., `uvicorn server.api.main:app --host 0.0.0.0 --port 8000`)
- Responsibilities:
  - Initialize FastAPI app with lifespan context
  - Create database connection pool on startup
  - Register route routers with prefix/tag mappings
  - Setup CORS middleware
  - Provide `/health` health check endpoint

**QGIS Plugin:**
- Location: `/home/rosen/fiberq/fiberq/__init__.py` → `main_plugin.py`
- Triggers: QGIS loads plugin at startup via `classFactory(iface)` function
- Responsibilities:
  - Initialize StuboviPlugin class with QGIS interface
  - Register menu items and toolbar buttons
  - Load all addons
  - Setup language support and pro license check

**Sync Upload Endpoint:**
- Path: `POST /api/sync/upload?project_id={id}`
- Location: `/home/rosen/fiberq/server/api/sync/routes.py`
- Triggers: User selects GPKG file and clicks sync upload in QField
- Responsibilities: Receive file, merge into PostGIS, log sync operation

**Fiber Plan Dialog:**
- Location: `/home/rosen/fiberq/fiberq/addons/fiber_plan.py` `SpliceClosureDialog`
- Triggers: User clicks "FiberQ → Fiber Plan" menu item
- Responsibilities: Manage splice closures and trays, display splice matrix, trace fiber paths

## Error Handling

**Strategy:**
- Server: Exceptions converted to HTTP status codes (400 Bad Request, 403 Forbidden, 404 Not Found, 500 Internal Server Error)
- Client: Exceptions caught in addons, displayed as QMessageBox dialogs to user
- Both: Errors logged with context for debugging

**Patterns:**

**Server-side (FastAPI):**
```python
# In routes.py
from fastapi import HTTPException

@router.post("/closures", response_model=SpliceClosureOut, status_code=201)
async def create_closure(body: SpliceClosureCreate, user: UserInfo = Depends(require_any_role)):
    pool = get_pool()
    try:
        row = await pool.fetchrow("""INSERT INTO ...""", ...)
        return SpliceClosureOut(**dict(row))
    except Exception as e:
        logger.exception("Failed to create closure")
        raise HTTPException(status_code=500, detail="Database error")
```

**Client-side (QGIS Plugin):**
```python
# In addon dialog
try:
    client = _get_api_client()
    data = client.get(f"/projects/{project_id}")
except RuntimeError as e:
    QMessageBox.critical(self, "API Error", str(e))
```

**Database-level:**
```python
# In sync/merger.py
async with pool.acquire() as conn:
    async with conn.transaction():
        # All operations within transaction; automatic rollback on error
        result = await _merge_layer(conn, gpkg_path, layer_name, table, ...)
```

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module
- Config: Set in `main.py` lifespan based on `settings.log_level` (default: "info")
- Pattern: Named loggers per module (e.g., `logging.getLogger("fiberq.sync.merger")`)
- Output: Logs to console in container, captured by Docker/orchestration

**Validation:**
- Request bodies: Pydantic models with type hints (e.g., `ProjectCreate`)
- Query parameters: FastAPI auto-validates via parameter types
- Database: asyncpg handles type coercion; schema constraints enforced in SQL
- File uploads: MIME type and extension checks in route handlers

**Authentication:**
- Bearer token in `Authorization: Bearer <token>` header
- Token validated against Zitadel OIDC provider on each request
- JWT claims extracted for user identity
- Role-based access control via `require_admin()`, `require_engineer()`, `require_field_worker()` dependencies

**Authorization:**
- Routes depend on role functions that raise 403 HTTPException if unauthorized
- Example: `/projects` POST requires engineer or admin role
- Example: `/fiber-plan/closures` requires any authenticated user (field_worker+)

**Database Transactions:**
- Sync merge operations use `async with conn.transaction()` to ensure atomicity
- Auto-rollback on exception
- Schema search_path set to fiberq schema on pool creation

---

*Architecture analysis: 2026-02-21*

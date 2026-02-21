# Codebase Structure

**Analysis Date:** 2026-02-21

## Directory Layout

```
/home/rosen/fiberq/
├── fiberq/                      # QGIS plugin package (installable as plugin)
│   ├── __init__.py              # Plugin entry point (classFactory)
│   ├── main_plugin.py           # Main plugin class (12,991 lines) - monolithic UI
│   ├── config.ini               # Server config (api_url, auth settings)
│   ├── metadata.txt             # QGIS plugin metadata (version, author, etc)
│   ├── addons/                  # Modular feature addons
│   │   ├── api_client.py        # HTTP client for server communication
│   │   ├── zitadel_auth.py      # OIDC authentication
│   │   ├── fiber_plan.py        # Splice closure management dialog
│   │   ├── fiber_break.py       # Fiber break detection tool
│   │   ├── work_orders.py       # Work order management
│   │   ├── fiberq_preview.py    # Preview/preview mode dialog
│   │   ├── publish_pg.py        # PostgreSQL publication dialog
│   │   ├── infrastructure_cut.py # Infrastructure cut tool
│   │   ├── reserve_hook.py      # Reserve hook handler
│   │   ├── settings.py          # Settings dialog
│   │   ├── styles.py            # Style application dialog
│   │   └── hotkeys.py           # Keyboard shortcuts
│   ├── icons/                   # Icon assets (.png files)
│   ├── styles/                  # QGIS style files
│   └── resources/               # Additional resources
│       └── map_icons/           # Map-specific icons
│
├── server/                      # Server/API implementation
│   ├── api/                     # FastAPI application
│   │   ├── main.py              # FastAPI app instance, router setup, lifespan
│   │   ├── config.py            # Settings/config management
│   │   ├── database.py          # AsyncPG connection pool
│   │   ├── dependencies.py      # FastAPI dependency injection
│   │   ├── requirements.txt     # Python dependencies (fastapi, asyncpg, etc)
│   │   ├── Dockerfile           # Container image definition
│   │   │
│   │   ├── auth/                # Authentication & authorization
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Pydantic models (UserInfo, TokenInfo)
│   │   │   ├── routes.py        # Auth endpoints (/me, /roles)
│   │   │   ├── zitadel.py       # OIDC token validation
│   │   │   └── roles.py         # Role-based access control decorators
│   │   │
│   │   ├── projects/            # Project management
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Pydantic models (ProjectCreate, ProjectOut)
│   │   │   └── routes.py        # Project CRUD endpoints
│   │   │
│   │   ├── sync/                # GeoPackage synchronization
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # Sync endpoints (/upload, /download)
│   │   │   ├── merger.py        # GPKG→PostGIS merge logic (timestamp-based)
│   │   │   ├── exporter.py      # PostGIS→GPKG export logic
│   │   │   └── differ.py        # Change detection for sync protocol
│   │   │
│   │   ├── fiber_plan/          # Fiber optic network management
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Pydantic models (SpliceClosure, SpliceTray, etc)
│   │   │   ├── routes.py        # Fiber plan endpoints (/closures, /splices, /trace)
│   │   │   └── tracer.py        # Fiber path tracing via PostGIS
│   │   │
│   │   └── work_orders/         # Work order management
│   │       ├── __init__.py
│   │       ├── models.py        # Pydantic models (WorkOrder, SMRReport)
│   │       └── routes.py        # Work order endpoints, SMR reports
│   │
│   ├── db/                      # Database scripts & schema
│   │   └── init.sql             # PostgreSQL schema initialization (tables, indexes)
│   │
│   ├── nginx/                   # Reverse proxy configuration
│   │   └── nginx.conf           # Nginx config for API routing
│   │
│   ├── docker-compose.yml       # Production composition (API, DB, cache)
│   └── docker-compose.dev.yml   # Development composition
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests (empty structure)
│   └── qgis/                    # QGIS integration tests (empty structure)
│
├── tools/                       # Utility scripts
│   └── qfield_forms/            # QField form generation tools
│       └── generate_qfield_project.py
│
├── .github/                     # GitHub configuration
│   └── workflows/               # CI/CD pipelines (empty)
│
├── .planning/                   # GSD planning documents
│   └── codebase/                # Codebase analysis docs
│
└── .gitignore                   # Git exclusions
```

## Directory Purposes

**`/home/rosen/fiberq/fiberq/`:**
- Purpose: QGIS plugin package distributed to users
- Contains: Plugin entry point, monolithic main plugin class, modular addons, assets
- Key files: `main_plugin.py` (UI controller), `__init__.py` (plugin factory)
- Installation: Copied to `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/fiberq/` on user machines

**`/home/rosen/fiberq/fiberq/addons/`:**
- Purpose: Pluggable feature modules loaded conditionally by main plugin
- Contains: Dialog and tool classes, each addon is self-contained
- Pattern: Each file implements one feature area with UI initialization
- Loading: Imported and instantiated in `main_plugin.py` based on user interactions

**`/home/rosen/fiberq/server/api/`:**
- Purpose: FastAPI server application code
- Contains: Route handlers, models, business logic, database interface
- Architecture: Layered with clear separation of concerns (routes → models → domain logic)
- Deployment: Containerized via Dockerfile, runs in production with asyncio + Uvicorn

**`/home/rosen/fiberq/server/api/auth/`:**
- Purpose: Authentication and authorization layer
- Contains: Zitadel OIDC integration, JWT validation, role-based access control
- Key functions: `get_current_user()` (FastAPI dependency), `validate_token()` (JWT validation)
- Reused: Every authenticated endpoint depends on `get_current_user()`

**`/home/rosen/fiberq/server/api/sync/`:**
- Purpose: GeoPackage ↔ PostGIS synchronization logic
- Contains: Upload/download endpoints, feature-level merge algorithm, change detection
- Core algorithm: Timestamp-based conflict resolution (newer timestamp wins)
- Layer mapping: `LAYER_TABLE_MAP` bridges QField layer names to database tables

**`/home/rosen/fiberq/server/api/fiber_plan/`:**
- Purpose: Fiber optic splice closure and path management
- Contains: CRUD endpoints for closures/trays/splices, fiber path tracing
- Spatial operations: PostGIS queries for path connectivity
- Related QGIS addon: `fiber_plan.py` (UI for splice management)

**`/home/rosen/fiberq/server/db/`:**
- Purpose: Database schema and initialization
- Contains: Single `init.sql` file with CREATE TABLE, indexes, constraints
- Deployment: Run during database provisioning in `docker-compose.yml`
- Schema: Tables prefixed with `ftth_` (fiber-to-the-home) convention

**`/home/rosen/fiberq/tests/`:**
- Purpose: Test infrastructure (currently empty; no test implementations)
- Structure: Split into `unit/` (single-component) and `qgis/` (integration) subdirectories
- Note: Tests not yet implemented; directories reserved for future work

## Key File Locations

**Entry Points:**

- `fiberq/__init__.py`: QGIS plugin factory entry point (required interface)
  ```python
  def classFactory(iface):
      from .main_plugin import StuboviPlugin
      return StuboviPlugin(iface)
  ```
- `server/api/main.py`: FastAPI app instance and route registration

**Configuration:**

- `fiberq/config.ini`: Plugin-side server config (api_url, zitadel_domain, client_id)
- `server/api/config.py`: Server-side settings via Pydantic (database_url, auth, storage paths)
- `.env` file (not in repo): Runtime environment variables for server (see `.env.example`)

**Core Logic:**

- `fiberq/main_plugin.py`: Monolithic QGIS plugin UI (dialogs, map tools, event handling)
- `server/api/sync/merger.py`: Feature-level merge algorithm (204 lines)
- `server/api/fiber_plan/tracer.py`: Fiber path tracing (158 lines)
- `server/api/sync/differ.py`: Change detection (322 lines)

**Database Access:**

- `server/api/database.py`: AsyncPG connection pool management
- `server/db/init.sql`: SQL schema with tables, indexes, constraints

**Authentication:**

- `fiberq/addons/zitadel_auth.py`: QGIS plugin-side OIDC client
- `server/api/auth/zitadel.py`: Server-side JWT validation
- `server/api/auth/roles.py`: Role hierarchy and access control decorators

## Naming Conventions

**Files:**

- **Python modules**: `snake_case.py` (e.g., `api_client.py`, `fiber_plan.py`, `main_plugin.py`)
- **Classes**: `PascalCase` (e.g., `FiberQApiClient`, `SpliceClosureDialog`, `UserInfo`)
- **Functions/methods**: `snake_case` (e.g., `merge_gpkg_to_postgis()`, `_load_server_config()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `LAYER_TABLE_MAP`, `_FIBERQ_PRO_MASTER_KEY`)
- **Private functions**: Prefix with `_` (e.g., `_get_api_client()`, `_build_ui()`)

**Directories:**

- **Feature modules**: `snake_case` (e.g., `fiber_plan/`, `work_orders/`, `sync/`)
- **Layer directories**: Semantic names matching content (e.g., `api/`, `auth/`, `db/`)

**Database:**

- **Tables**: `ftth_<feature>` convention (e.g., `ftth_okna`, `ftth_stubovi`, `ftth_kablovi_podzemni`)
- **Columns**: `snake_case` (e.g., `created_at`, `_modified_by_sub`, `closure_type`)
- **Audit columns**: Prefix with `_` to denote system-managed fields (e.g., `_modified_at`, `_modified_by_sub`)

**Routes:**

- **Prefix-based grouping**: `/auth`, `/projects`, `/sync`, `/fiber-plan`, `/work-orders`
- **Resource-oriented**: GET /projects, POST /projects, GET /projects/{id}, PUT /projects/{id}
- **Action endpoints**: POST /sync/upload, GET /fiber-plan/trace

## Where to Add New Code

**New Feature (complete flow from UI to API):**

1. **Server-side:**
   - Create new module directory: `server/api/my_feature/`
   - Add `models.py` with Pydantic schemas (Create, Update, Out)
   - Add `routes.py` with APIRouter and endpoints
   - Add domain logic to separate file if complex (e.g., `my_feature/service.py`)
   - Register router in `server/api/main.py`: `app.include_router(router, prefix="/my-feature")`

2. **Client-side:**
   - Create addon file: `fiberq/addons/my_feature.py`
   - Implement dialog or tool class (inherit QDialog or QgsMapTool)
   - Use `FiberQApiClient` to call server endpoints
   - Register in `main_plugin.py` main menu/toolbar

3. **Database:**
   - Add table definitions to `server/db/init.sql`
   - Include `id` PRIMARY KEY, `_modified_at` TIMESTAMP, `_modified_by_sub` VARCHAR

Example structure for new feature:
```
server/api/my_feature/
├── __init__.py
├── models.py         # Pydantic schemas
├── routes.py         # Endpoint definitions
└── service.py        # Business logic (if needed)
```

**New Component/Module:**

- **Within existing feature:** Add file to feature directory (e.g., `fiber_plan/utils.py`)
- **Shared utilities:** Create `server/api/common/` or `server/api/utils.py`
- **Plugin utility:** Create in `fiberq/utilities/` or directly in addon file if tightly coupled

**Utilities:**

- **Server-side shared helpers:** `server/api/common/` directory
- **Client-side shared helpers:** `fiberq/utilities/` directory (currently empty)
- **SQL utilities:** Functions in `server/db/` subdirectory (currently just init.sql)

**Example: Adding sync for new feature type:**

1. Add table to `init.sql`: `CREATE TABLE ftth_my_features (...)`
2. Add to `LAYER_TABLE_MAP` in `sync/merger.py`: `"MyFeatures": "ftth_my_features"`
3. Sync will automatically include the layer on next upload/download

## Special Directories

**`/home/rosen/fiberq/.planning/codebase/`:**
- Purpose: GSD codebase analysis documents
- Generated: By GSD `/gsd:map-codebase` commands
- Committed: Yes, tracked in git
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md, INTEGRATIONS.md, STACK.md

**`/home/rosen/fiberq/fiberq/icons/`:**
- Purpose: Application UI icons (toolbars, buttons)
- Format: PNG files referenced by `_load_icon()` in `main_plugin.py`
- Generated: No, hand-created assets
- Committed: Yes

**`/home/rosen/fiberq/fiberq/styles/`:**
- Purpose: QGIS layer styling (symbology, labeling)
- Format: QGIS .qml files
- Generated: By QGIS GUI, committed for version control
- Committed: Yes

**`/home/rosen/fiberq/server/db/`:**
- Purpose: Database initialization and schema
- Files: `init.sql` (13,117 bytes)
- Generated: No, hand-written DDL
- Committed: Yes, critical for deployment

**`/home/rosen/fiberq/.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes, created by `python -m venv .venv`
- Committed: No, in .gitignore
- Usage: Development and testing environment

**`/home/rosen/fiberq/.pytest_cache/`:**
- Purpose: pytest test cache
- Generated: Yes, by pytest on test runs
- Committed: No, in .gitignore

**`/home/rosen/fiberq/.env` (server/):**
- Purpose: Runtime environment variables
- Generated: Copy from `.env.example` and customize
- Committed: No, contains secrets
- Note: Never commit actual .env file; use .env.example as template

---

*Structure analysis: 2026-02-21*

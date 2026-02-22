---
phase: 02-user-management
plan: 01
subsystem: api
tags: [kanidm, fastapi, httpx, pydantic, user-management, oidc, postgresql]

# Dependency graph
requires:
  - phase: 01-auth-app-shell
    provides: "Kanidm OIDC auth, FastAPI skeleton, auth.ts jwt callback, init.sql schema"
provides:
  - "KanidmAdminClient for Kanidm V1 REST API admin operations"
  - "FastAPI /users router with 7 CRUD endpoints (list, get, create, deactivate, reactivate, update-roles, reset-password)"
  - "Pydantic models for user CRUD (UserCreate, UserRoleUpdate, UserOut, UserListOut, CredentialResetOut)"
  - "user_logins table for last login tracking"
  - "POST /auth/record-login endpoint for login event recording"
  - "auth.ts fire-and-forget record-login call on sign-in"
affects: [02-user-management, 03-project-management]

# Tech tracking
tech-stack:
  added: [httpx (async Kanidm API calls)]
  patterns: [admin API proxy via service account token, fire-and-forget login tracking, upsert login events]

key-files:
  created:
    - server/api/users/__init__.py
    - server/api/users/kanidm_client.py
    - server/api/users/models.py
    - server/api/users/routes.py
  modified:
    - server/api/config.py
    - server/api/main.py
    - server/api/auth/routes.py
    - server/db/init.sql
    - web/src/auth.ts

key-decisions:
  - "KanidmAdminClient as plain class instantiated per-request via factory function"
  - "INTERNAL_API_URL env var for server-side auth.ts record-login call (same as apiFetch utility)"
  - "Fire-and-forget login tracking pattern -- never blocks sign-in flow"

patterns-established:
  - "Kanidm admin proxy: routes.py -> kanidm_client.py -> Kanidm V1 API"
  - "Role group naming convention: fiberq_{role} in Kanidm, stripped to {role} in app"
  - "Login tracking via upsert into user_logins table on each WebUI sign-in"

# Metrics
duration: 4min
completed: 2026-02-21
---

# Phase 2 Plan 01: User Management Backend Summary

**Kanidm admin API proxy with 7 FastAPI endpoints for user CRUD, role management, and last login tracking via PostgreSQL**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-21T21:00:42Z
- **Completed:** 2026-02-21T21:04:53Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- KanidmAdminClient with 12 async methods covering all Kanidm V1 person and group operations
- FastAPI /users router with 7 admin-only endpoints: list, get, create, deactivate, reactivate, update-roles, reset-password
- user_logins table and POST /auth/record-login endpoint for last login tracking
- auth.ts jwt callback wired to fire-and-forget POST on initial sign-in

## Task Commits

Each task was committed atomically:

1. **Task 1: Kanidm admin client and Pydantic models** - `6e1e89c` (feat)
2. **Task 2: FastAPI /users router with all CRUD endpoints** - `97af96c` (feat)
3. **Task 3: Last login tracking and auth callback wiring** - `31fd7d3` (feat)

## Files Created/Modified
- `server/api/users/__init__.py` - Package init
- `server/api/users/kanidm_client.py` - Async Kanidm V1 REST API client with 12 methods
- `server/api/users/models.py` - Pydantic models: UserCreate, UserRoleUpdate, UserOut, UserListOut, CredentialResetOut
- `server/api/users/routes.py` - FastAPI /users router with 7 admin-only endpoints
- `server/api/config.py` - Added kanidm_api_token field to Settings
- `server/api/main.py` - Registered users router under /users prefix
- `server/api/auth/routes.py` - Added POST /auth/record-login endpoint with upsert logic
- `server/db/init.sql` - Added user_logins table with index on last_login_at
- `web/src/auth.ts` - Added fire-and-forget fetch to record-login on initial sign-in

## Decisions Made
- KanidmAdminClient instantiated per-request via `_get_kanidm_client()` factory (simple, no singleton complexity)
- Used `INTERNAL_API_URL` env var (same as apiFetch in web/src/lib/api.ts) for server-side record-login call
- Fire-and-forget pattern for login tracking: `.catch(() => {})` ensures sign-in flow is never blocked
- Used `require_admin` from `auth.roles` (not `dependencies.py`) for consistency with the role factory pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `fiona` module not installed locally caused `from main import app` to fail during full-app verification. This is pre-existing and unrelated to our changes (fiona is a GIS library used by sync module). Verified all user-management modules independently instead.

## User Setup Required
None - no external service configuration required. The `KANIDM_API_TOKEN` environment variable must be set in the deployment environment, but this is an existing operational concern documented in the project config.

## Next Phase Readiness
- Backend user CRUD endpoints ready for Plan 02 (frontend user management UI)
- All endpoints are admin-only, awaiting frontend integration via Server Actions
- user_logins tracking active, last login data will populate on next WebUI sign-in

## Self-Check: PASSED

All 10 files verified present. All 3 task commits verified in git log.

---
*Phase: 02-user-management*
*Completed: 2026-02-21*

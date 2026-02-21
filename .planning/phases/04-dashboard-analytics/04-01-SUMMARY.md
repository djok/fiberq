---
phase: 04-dashboard-analytics
plan: 01
subsystem: api
tags: [fastapi, asyncpg, postgresql, union-all, cursor-pagination, activity-log]

# Dependency graph
requires:
  - phase: 03-project-management
    provides: "projects CRUD, project_users assignment, project detail endpoint"
provides:
  - "GET /projects/{id}/stats endpoint with element counts, team size, last sync"
  - "GET /projects/{id}/activity endpoint with paginated multi-source feed"
  - "project_activity_log table for status changes and member removals"
  - "Activity logging wired into update_project and remove_member mutations"
affects: [04-02-PLAN (frontend dashboard consumes these endpoints)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UNION ALL count aggregation across infrastructure tables for stats"
    - "Cursor-based pagination with ISO timestamp 'before' parameter"
    - "UNION ALL multi-source activity feed (sync_log + project_users + activity_log)"
    - "_check_project_visibility helper for reusable auth/existence checks"
    - "Pre-delete data capture for activity logging (fetch before DELETE)"

key-files:
  created: []
  modified:
    - "server/db/init.sql"
    - "server/api/projects/models.py"
    - "server/api/projects/routes.py"

key-decisions:
  - "Stats return null for counts when no completed sync_log entry exists (not 0) -- distinguishes 'no data' from 'zero elements'"
  - "Activity feed skips assignment logging to project_activity_log to avoid duplicate events (assignments already queryable from project_users table)"
  - "Route ordering: stats and activity endpoints defined before /{project_id} detail to prevent FastAPI route shadowing"

patterns-established:
  - "_check_project_visibility: reusable project existence + access check helper"
  - "Pre-mutation data capture: fetch old state before UPDATE/DELETE for activity logging"
  - "UNION ALL aggregation with source aliases for single-query multi-table counts"

# Metrics
duration: 3min
completed: 2026-02-22
---

# Phase 4 Plan 01: Project Stats & Activity API Summary

**Two new API endpoints (stats with UNION ALL element counts, paginated activity feed) plus activity logging in existing mutations via project_activity_log table**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-21T23:46:20Z
- **Completed:** 2026-02-21T23:49:42Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- GET /projects/{id}/stats returns closures, poles, cables, cable_length_m, team_size, last_sync_at, last_sync_features in a single response with null counts when no sync data exists
- GET /projects/{id}/activity returns paginated activity entries combining sync_log, project_users, and project_activity_log via UNION ALL with cursor-based pagination
- Status changes and member removals are now recorded in project_activity_log for the activity feed
- project_activity_log table created with FK cascade, composite index, and grants

## Task Commits

Each task was committed atomically:

1. **Task 1: Add project_activity_log table and Pydantic models** - `eec4423` (feat)
2. **Task 2: Add stats/activity endpoints and activity logging** - `1250db9` (feat)

## Files Created/Modified
- `server/db/init.sql` - Added project_activity_log table with index and grants
- `server/api/projects/models.py` - Added ProjectStats, ActivityEntry, ActivityPage Pydantic models
- `server/api/projects/routes.py` - Added GET /stats, GET /activity endpoints; wired status_change and member_removed logging into update_project and remove_member

## Decisions Made
- Stats use sync_log existence check (not element count check) to determine has_data -- a completed sync with zero elements still shows "0" not null
- Activity feed does NOT log member_assigned to project_activity_log to avoid duplicates (assignments are already queryable from project_users table in the UNION)
- Route ordering enforced: stats and activity defined before the /{project_id} catch-all detail route
- Extracted _check_project_visibility helper for DRY visibility checks across stats, activity, and detail endpoints

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Stats and activity endpoints are ready for frontend consumption in plan 04-02
- Frontend can call GET /projects/{id}/stats and GET /projects/{id}/activity?limit=20 with existing auth tokens
- Cursor pagination via `before` query param supports "Load more" button implementation

## Self-Check: PASSED

- All 3 modified files exist on disk
- Both task commits (eec4423, 1250db9) found in git log
- All new models and endpoints import successfully

---
*Phase: 04-dashboard-analytics*
*Completed: 2026-02-22*

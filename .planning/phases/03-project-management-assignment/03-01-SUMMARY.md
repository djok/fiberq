---
phase: 03-project-management-assignment
plan: 01
subsystem: api, database
tags: [fastapi, asyncpg, postgis, pydantic, rbac, junction-table]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "Auth middleware, role dependencies, FastAPI router patterns"
  - phase: 02-user-management
    provides: "user_logins table for assignable-users endpoint"
provides:
  - "project_users junction table for user-to-project assignment"
  - "Status column on projects (planning/in_progress/completed/paused/archived)"
  - "Role-scoped project listing (admin/PM see all, others see assigned)"
  - "PostGIS extent computation via batch UNION ALL across 9 infrastructure tables"
  - "Assignment CRUD endpoints (assign, remove, list assignable users)"
  - "ProjectDetailOut with members list and computed extent"
  - "require_project_manager_or_admin role dependency"
affects: [03-02, 03-03, 04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Batch PostGIS extent via UNION ALL grouped by project_id"
    - "Permission helper combining global role + project-level role DB lookup"
    - "Upsert pattern (ON CONFLICT DO UPDATE) for member assignment"
    - "Denormalized user_display_name/user_email in junction table"

key-files:
  created: []
  modified:
    - "server/db/init.sql"
    - "server/api/projects/models.py"
    - "server/api/projects/routes.py"
    - "server/api/auth/roles.py"

key-decisions:
  - "Denormalized user display name and email into project_users to avoid Kanidm lookups on every listing"
  - "Batch extent computation in list endpoint to avoid N+1 queries"
  - "assignable-users endpoint queries user_logins table as pragmatic shortcut for known users"
  - "Upsert pattern for member assignment allows re-assigning with different role"

patterns-established:
  - "_check_project_manager_permission: reusable helper for admin OR global PM OR project-level manager"
  - "_build_extent_union_query: generates UNION ALL across all 9 infrastructure tables"
  - "member_names on ProjectOut for client-side filtering by assigned user"

# Metrics
duration: 2min
completed: 2026-02-22
---

# Phase 3 Plan 01: Project API with Status, Assignment, and PostGIS Extent Summary

**project_users junction table with role-scoped listing, assignment CRUD, and batch PostGIS extent computation across 9 infrastructure tables**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-21T22:41:27Z
- **Completed:** 2026-02-21T22:43:56Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Database schema extended with project_users junction table (CHECK constraint on roles, UNIQUE on project_id+user_sub, indexes) and status column on projects
- 6 Pydantic models (ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut, ProjectMemberOut, AssignMemberBody) plus PROJECT_STATUSES and PROJECT_ROLES constants
- 8 API endpoints: role-scoped list, create, detail with members/extent, update with status, delete, assign member (upsert), remove member, assignable users
- PostGIS extent computed via batch UNION ALL query across all 9 infrastructure tables, with fallback to project bounds_geom

## Task Commits

Each task was committed atomically:

1. **Task 1: Add project_users table and status column + update models** - `c6e0817` (feat)
2. **Task 2: Extend project routes with 8 endpoints** - `5c5f585` (feat)

## Files Created/Modified
- `server/db/init.sql` - Added project_users table, status column ALTER, grants
- `server/api/projects/models.py` - Extended with 6 models and 2 constants
- `server/api/projects/routes.py` - Rewritten with 8 endpoints, permission helper, batch extent computation
- `server/api/auth/roles.py` - Added require_project_manager_or_admin dependency

## Decisions Made
- **Denormalized user data in project_users:** user_display_name and user_email stored in junction table to avoid Kanidm lookups. Acceptable tradeoff for small team (50-200 users) where name changes are rare.
- **Batch extent in list endpoint:** Single UNION ALL query grouped by project_id instead of N separate queries. Avoids N+1 problem on project cards page.
- **assignable-users from user_logins:** Queries the user_logins table (all users who have ever logged in) rather than calling Kanidm API. Pragmatic shortcut that avoids external API dependency.
- **Upsert for assignment:** ON CONFLICT DO UPDATE allows re-assigning a user with a different role without requiring delete+insert.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend API fully supports project CRUD with status, user assignment with project-level roles, and PostGIS extent
- Ready for Plan 02 (frontend project cards with mini-maps) and Plan 03 (project detail page with member management)
- Database migration (ALTER TABLE + CREATE TABLE) needs to run against existing databases

## Self-Check: PASSED

All 4 files verified present. Both commit hashes (c6e0817, 5c5f585) found in git log.

---
*Phase: 03-project-management-assignment*
*Completed: 2026-02-22*

---
phase: 05-tech-debt-cleanup
plan: 01
subsystem: infra
tags: [middleware, nextjs, dead-code, auth-guard]

# Dependency graph
requires:
  - phase: 01-auth-shell
    provides: Auth.js v5 proxy.ts file and auth() pattern
provides:
  - Edge middleware properly named for Next.js convention loading
  - Removed dead code (dependencies.py)
  - Consistent per-page auth guard on dashboard
affects: [05-02]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Next.js middleware at src/middleware.ts (convention-based Edge loading)"
    - "Per-page auth guard: auth() + redirect on all protected pages"

key-files:
  created: []
  modified:
    - web/src/middleware.ts
    - web/src/app/[locale]/dashboard/page.tsx

key-decisions:
  - "No code changes to middleware logic -- rename only to satisfy Next.js convention"
  - "Dashboard auth guard is consistency fix, not security fix (layout already protects)"

patterns-established:
  - "Every protected page must have its own auth() + redirect guard (defense in depth)"

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 5 Plan 1: Quick Tech Debt Fixes Summary

**Renamed proxy.ts to middleware.ts for Edge loading, deleted orphaned dependencies.py, added per-page auth guard to dashboard**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-22T00:35:04Z
- **Completed:** 2026-02-22T00:39:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Renamed `web/src/proxy.ts` to `web/src/middleware.ts` so Next.js loads it as Edge middleware (was silently ignored)
- Deleted `server/api/dependencies.py` -- 31 lines of dead code superseded by `auth/roles.py` factory function
- Added `auth()` + `redirect()` guard to `dashboard/page.tsx` matching the pattern on all other protected pages

## Task Commits

Each task was committed atomically:

1. **Task 1: Rename proxy.ts to middleware.ts** - `5d7e70a` (refactor)
2. **Task 2: Delete dependencies.py dead code** - `c86e70e` (chore)
3. **Task 3: Add auth() check to dashboard page** - `9100c21` (fix)

## Files Created/Modified
- `web/src/middleware.ts` - Edge middleware with auth + i18n composition (renamed from proxy.ts, updated JSDoc and function name)
- `server/api/dependencies.py` - Deleted (hardcoded role checks replaced by auth/roles.py)
- `web/src/app/[locale]/dashboard/page.tsx` - Added auth() session check + redirect guard

## Decisions Made
- No code changes to middleware logic -- rename only to satisfy Next.js convention
- Dashboard auth guard is a consistency fix, not a security fix (layout-level guard already protected it)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 3 of 5 tech debt items from v1 milestone audit are now closed
- Plan 05-02 (remaining 2 items) can proceed independently
- TypeScript compilation verified clean after all changes

## Self-Check: PASSED

- FOUND: web/src/middleware.ts
- DELETED: web/src/proxy.ts
- DELETED: server/api/dependencies.py
- FOUND: dashboard/page.tsx (with auth guard)
- FOUND: 05-01-SUMMARY.md
- FOUND commit: 5d7e70a (Task 1)
- FOUND commit: c86e70e (Task 2)
- FOUND commit: 9100c21 (Task 3)

---
*Phase: 05-tech-debt-cleanup*
*Completed: 2026-02-22*

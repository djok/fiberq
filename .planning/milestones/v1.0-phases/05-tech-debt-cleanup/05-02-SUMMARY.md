---
phase: 05-tech-debt-cleanup
plan: 02
subsystem: api, ui
tags: [kanidm, fastapi, nextjs, i18n, confirmation-dialog, server-actions]

# Dependency graph
requires:
  - phase: 03-project-management
    provides: assignable-users endpoint, project detail page with actions card
  - phase: 02-user-management
    provides: KanidmAdminClient, ConfirmActionDialog pattern
provides:
  - Kanidm-backed assignable users endpoint (all persons, not just logged-in)
  - Delete project UI with confirmation dialog and redirect
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Cross-module ConfirmActionDialog reuse for destructive project actions
    - Kanidm list_persons as source of truth for user enumeration

key-files:
  created: []
  modified:
    - server/api/projects/routes.py
    - web/src/app/[locale]/projects/_actions.ts
    - web/src/app/[locale]/projects/_components/project-detail-actions.tsx
    - web/src/messages/en.json
    - web/src/messages/bg.json

key-decisions:
  - "Assignable users sourced from Kanidm list_persons with spn as user_sub (matches Auth.js sub claim)"
  - "Delete button uses same ConfirmActionDialog from users module (cross-module import pattern)"
  - "Post-delete redirect to projects list via router.push with locale prefix"

patterns-established:
  - "Kanidm as single source of truth for user enumeration across all endpoints"

# Metrics
duration: 3min
completed: 2026-02-22
---

# Phase 5 Plan 2: Tech Debt Code Fixes Summary

**Kanidm-backed assignable users replacing user_logins query, plus delete project button with confirmation dialog and i18n**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-22T00:35:06Z
- **Completed:** 2026-02-22T00:38:37Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Assignable users endpoint now fetches all Kanidm persons instead of only logged-in users from user_logins table
- Delete Project button with confirmation dialog on project detail page, gated by canManage permission
- Full EN and BG i18n support for delete confirmation flow

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix assignable users to source from Kanidm** - `e5aad4e` (feat)
2. **Task 2: Add project delete button with confirmation dialog** - `5711396` (feat)

**Plan metadata:** (pending) (docs: complete plan)

## Files Created/Modified
- `server/api/projects/routes.py` - Replaced user_logins query with KanidmAdminClient.list_persons(), added kanidm imports and factory
- `web/src/app/[locale]/projects/_actions.ts` - Added deleteProject server action calling DELETE /projects/{id}
- `web/src/app/[locale]/projects/_components/project-detail-actions.tsx` - Added Delete button, ConfirmActionDialog, useRouter redirect, toast notifications
- `web/src/messages/en.json` - Added deleteProject, confirmDeleteTitle, confirmDeleteDescription, deleteSuccess, deleteError keys
- `web/src/messages/bg.json` - Added Bulgarian translations for all delete-related keys

## Decisions Made
- Used `spn` attribute from Kanidm (format: `username@domain`) as `user_sub` -- matches what Auth.js receives in the sub claim
- Reused ConfirmActionDialog from users module via cross-module import (same pattern as Phase 3 member removal)
- Post-delete redirect uses `router.push` with locale prefix to navigate to projects list

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both tech debt code items from v1 milestone audit are now resolved
- Assignable users sources from Kanidm (all persons visible without requiring first login)
- Project deletion available via UI with proper confirmation flow

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 05-tech-debt-cleanup*
*Completed: 2026-02-22*

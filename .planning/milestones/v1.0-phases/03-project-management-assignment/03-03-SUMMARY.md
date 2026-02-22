---
phase: 03-project-management-assignment
plan: 03
subsystem: ui
tags: [nextjs, maplibre-gl, shadcn, react-hook-form, zod, i18n, combobox, cmdk]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "Auth session with roles, sidebar navigation, i18n setup"
  - phase: 02-user-management
    provides: "Server Component + Client wrapper pattern, ConfirmActionDialog, discriminated union actions"
  - phase: 03-project-management-assignment
    plan: 01
    provides: "Project CRUD API with status, members, extent, assignment endpoints, assignable-users endpoint"
  - phase: 03-project-management-assignment
    plan: 02
    provides: "Project types, createProject action, ProjectMiniMap component, card grid with filters, shadcn command/popover/scroll-area"
provides:
  - "Project detail page at /projects/[id] with two-column layout"
  - "Interactive MapLibre map on detail page with NavigationControl"
  - "Member list with role badges, initials avatar, and removal with confirmation"
  - "Inline Command+Popover combobox for user search and role-based assignment"
  - "Edit project dialog with name, description, and status fields"
  - "Server actions: updateProject, assignMember, removeMember, fetchAssignableUsers"
affects: [04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Interactive MapLibre map via optional 'interactive' prop on ProjectMiniMap"
    - "Command+Popover combobox with lazy-loaded user list from server action"
    - "ConfirmActionDialog reuse across modules (users and projects)"
    - "ProjectDetailActions client wrapper for detail page interactive sections"

key-files:
  created:
    - "web/src/app/[locale]/projects/[id]/page.tsx"
    - "web/src/app/[locale]/projects/_components/project-detail-actions.tsx"
    - "web/src/app/[locale]/projects/_components/project-members.tsx"
    - "web/src/app/[locale]/projects/_components/member-combobox.tsx"
    - "web/src/app/[locale]/projects/_components/edit-project-dialog.tsx"
  modified:
    - "web/src/app/[locale]/projects/_actions.ts"
    - "web/src/app/[locale]/projects/_components/project-mini-map.tsx"

key-decisions:
  - "Reuse ConfirmActionDialog from Phase 2 users module for member removal confirmation"
  - "Interactive prop on ProjectMiniMap (default false) to differentiate detail page map from card mini-maps"
  - "Lazy-load assignable users via server action when combobox opens (not on page load)"
  - "canManage derived from admin, global project_manager, or project-level manager role"

patterns-established:
  - "ProjectDetailActions: client component bridge between server-fetched detail data and interactive dialogs/member management"
  - "MemberCombobox: Command+Popover with lazy server action fetch, role selection, and assign button"
  - "ProjectMiniMap interactive prop: NavigationControl added when interactive=true"

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 3 Plan 03: Project Detail Page with Interactive Map, Members, and Edit Dialog Summary

**Project detail page with interactive MapLibre map, inline Command+Popover combobox for member assignment, role-badged member list with removal confirmation, and edit project dialog**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-21T22:55:09Z
- **Completed:** 2026-02-21T22:59:11Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Built project detail page at /projects/[id] with two-column responsive layout (map + info left, members + actions right)
- Extended ProjectMiniMap with interactive prop: detail page map has NavigationControl for zoom/pan while card mini-maps remain static
- Created inline Command+Popover combobox that lazy-loads assignable users from server action with role selection (Manager/Specialist/Observer)
- Added 4 new server actions (updateProject, assignMember, removeMember, fetchAssignableUsers) following established discriminated union pattern
- Built edit project dialog with react-hook-form + zod validation for name, description, and status fields
- Reused ConfirmActionDialog from Phase 2 users module for member removal confirmation (no duplication)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add server actions for project update, member assignment, and member removal** - `524eddc` (feat)
2. **Task 2: Build project detail page with interactive map, members, and edit dialog** - `bed8365` (feat)

## Files Created/Modified
- `web/src/app/[locale]/projects/_actions.ts` - Extended with updateProject, assignMember, removeMember, fetchAssignableUsers server actions
- `web/src/app/[locale]/projects/[id]/page.tsx` - Server Component detail page with auth, API fetch, snake_case mapping, canManage logic
- `web/src/app/[locale]/projects/_components/project-detail-actions.tsx` - Client component bridging detail page with members card, actions card, and edit dialog
- `web/src/app/[locale]/projects/_components/project-members.tsx` - Members list with role badges, initials avatars, ScrollArea, and X remove button with ConfirmActionDialog
- `web/src/app/[locale]/projects/_components/member-combobox.tsx` - Inline Command+Popover combobox with lazy user fetch, role Select, and assign button
- `web/src/app/[locale]/projects/_components/edit-project-dialog.tsx` - Dialog with react-hook-form + zod for editing name, description, status
- `web/src/app/[locale]/projects/_components/project-mini-map.tsx` - Added optional interactive prop with NavigationControl

## Decisions Made
- **ConfirmActionDialog reuse:** Imported from `@/app/[locale]/users/_components/confirm-action-dialog` rather than duplicating. Cross-module import is acceptable since both are within the same app.
- **Interactive prop over separate component:** Added `interactive` prop (default false) to existing ProjectMiniMap instead of creating a separate interactive map component. Simpler, less code duplication.
- **Lazy user fetch on combobox open:** fetchAssignableUsers server action called when popover opens, not on page load. Avoids unnecessary API calls when user doesn't intend to assign anyone.
- **canManage from three sources:** admin role, global project_manager role, or project-level manager role in the fetched members list. Checked on server side and passed as boolean prop.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 complete: project management with card grid, detail page, member assignment, and editing fully operational
- Ready for Phase 4 (QGIS integration or remaining features)
- All project-related translation keys present in both EN and BG
- Interactive map foundation ready for future GIS features

## Self-Check: PASSED

All 7 files verified present. Both commit hashes (524eddc, bed8365) found in git log.

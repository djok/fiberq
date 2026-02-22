---
phase: 03-project-management-assignment
plan: 02
subsystem: ui
tags: [nextjs, maplibre-gl, postgis, shadcn, react-hook-form, zod, i18n]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "Auth session with roles, sidebar navigation, i18n setup"
  - phase: 02-user-management
    provides: "Server Component + Client wrapper pattern, discriminated union actions, DataTable conventions"
  - phase: 03-project-management-assignment
    plan: 01
    provides: "Project CRUD API with status, member_names, extent, assignment endpoints"
provides:
  - "Project list page with responsive card grid (1/2/3 columns)"
  - "PostGIS-driven mini-maps using MapLibre GL with Intersection Observer lazy loading"
  - "Client-side filtering by name search, status dropdown, and assigned user dropdown"
  - "Create project dialog with zod validation and server action"
  - "Role-scoped empty states (admin/PM vs regular user)"
  - "ProjectCard, ProjectDetail, ProjectMember, CreateProjectInput TypeScript types"
affects: [03-03, 04]

# Tech tracking
tech-stack:
  added: [maplibre-gl, "@types/geojson"]
  patterns:
    - "MapLibre GL inline OSM raster style (no external style.json)"
    - "Intersection Observer for lazy WebGL context creation to avoid browser limit (~16)"
    - "memberNames-based client-side user filtering derived from backend response"
    - "Server component fetches + maps snake_case, passes to client wrapper for interactive rendering"

key-files:
  created:
    - "web/src/types/project.ts"
    - "web/src/app/[locale]/projects/_actions.ts"
    - "web/src/app/[locale]/projects/_components/projects-client.tsx"
    - "web/src/app/[locale]/projects/_components/project-card.tsx"
    - "web/src/app/[locale]/projects/_components/project-mini-map.tsx"
    - "web/src/app/[locale]/projects/_components/create-project-dialog.tsx"
    - "web/src/components/ui/textarea.tsx"
    - "web/src/components/ui/command.tsx"
    - "web/src/components/ui/popover.tsx"
    - "web/src/components/ui/scroll-area.tsx"
  modified:
    - "web/src/app/[locale]/projects/page.tsx"
    - "web/src/messages/en.json"
    - "web/src/messages/bg.json"
    - "web/package.json"

key-decisions:
  - "MapLibre GL with inline OSM raster tiles for mini-maps (no external tile server needed)"
  - "Intersection Observer lazy loading to handle WebGL context limits with many cards"
  - "canCreate derived from admin or project_manager role on server side, passed as prop"
  - "Textarea component added via shadcn for project description input"

patterns-established:
  - "ProjectMiniMap: lazy-loaded MapLibre GL component with IntersectionObserver"
  - "Status badge color mapping utility for project statuses"
  - "Card grid with client-side multi-filter pattern (search + dropdown + dropdown)"

# Metrics
duration: 5min
completed: 2026-02-22
---

# Phase 3 Plan 02: Project List Page with Card Grid, Mini-Maps, and Filters Summary

**Card-based project list with MapLibre GL PostGIS mini-maps, triple client-side filtering (name/status/user), create dialog, and role-scoped empty states**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T22:47:03Z
- **Completed:** 2026-02-21T22:51:54Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Replaced placeholder projects page with fully functional card grid showing project name, status badge, member count, truncated description, and PostGIS mini-map
- Built MapLibre GL mini-map component with Intersection Observer for lazy WebGL context creation, preventing browser context limit issues with many cards
- Implemented three client-side filters: text search by name, status dropdown, and assigned user dropdown (derived from memberNames returned by backend)
- Created project dialog with react-hook-form + zod validation following Phase 2 discriminated union pattern
- Added all project-related translation keys to both EN and BG message files (30+ keys each including Plan 03 keys)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies, add shadcn components, create types and server actions** - `4b10782` (feat)
2. **Task 2: Build project list page with card grid, mini-map, filters, create dialog, and empty states** - `e522eec` (feat)

## Files Created/Modified
- `web/src/types/project.ts` - ProjectCard, ProjectDetail, ProjectMember, CreateProjectInput, AssignableUser types
- `web/src/app/[locale]/projects/page.tsx` - Server component fetching from /projects API with role check
- `web/src/app/[locale]/projects/_actions.ts` - createProject server action with discriminated union
- `web/src/app/[locale]/projects/_components/projects-client.tsx` - Client wrapper with filters, grid, empty states
- `web/src/app/[locale]/projects/_components/project-card.tsx` - Card with mini-map, status badge, member count
- `web/src/app/[locale]/projects/_components/project-mini-map.tsx` - MapLibre GL lazy-loaded mini-map
- `web/src/app/[locale]/projects/_components/create-project-dialog.tsx` - Modal dialog with zod validation
- `web/src/components/ui/textarea.tsx` - shadcn Textarea component
- `web/src/components/ui/command.tsx` - shadcn Command component (for Plan 03)
- `web/src/components/ui/popover.tsx` - shadcn Popover component (for Plan 03)
- `web/src/components/ui/scroll-area.tsx` - shadcn ScrollArea component (for Plan 03)
- `web/src/messages/en.json` - Added projects translation keys
- `web/src/messages/bg.json` - Added projects translation keys (Bulgarian)
- `web/package.json` - Added maplibre-gl dependency

## Decisions Made
- **MapLibre GL with inline OSM raster tiles:** No external tile server or style.json needed. Uses OpenStreetMap tiles directly in the style object, keeping deployment simple.
- **Intersection Observer for mini-maps:** Browsers limit WebGL contexts to ~16. The Intersection Observer only instantiates MapLibre maps when cards scroll into viewport, preventing context exhaustion with many project cards.
- **canCreate from roles:** Server component checks `session.user.roles` for "admin" or "project_manager" and passes boolean prop to client component. No client-side role checking needed.
- **Added Textarea component:** Plan mentioned "Textarea or Input multiline" for description. Added shadcn Textarea for better UX with project descriptions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added shadcn Textarea component**
- **Found during:** Task 2 (Create dialog implementation)
- **Issue:** Textarea component was not installed but needed for project description input
- **Fix:** Ran `npx shadcn@latest add textarea --yes`
- **Files modified:** web/src/components/ui/textarea.tsx
- **Verification:** Build passes, component renders correctly
- **Committed in:** e522eec (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor -- plan explicitly mentioned "Textarea or Input multiline" as an option. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Project list page fully functional with cards, mini-maps, filters, and create dialog
- Ready for Plan 03 (project detail page with member management and edit functionality)
- shadcn command/popover/scroll-area components pre-installed for Plan 03 user search combobox
- All translation keys for Plan 03 already included in both EN and BG message files

## Self-Check: PASSED

All 14 files verified present. Both commit hashes (4b10782, e522eec) found in git log.

---
*Phase: 03-project-management-assignment*
*Completed: 2026-02-22*

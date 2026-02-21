---
phase: 04-dashboard-analytics
plan: 02
subsystem: ui
tags: [next.js, react, next-intl, shadcn, lucide, server-components, client-components, cursor-pagination]

# Dependency graph
requires:
  - phase: 04-dashboard-analytics
    plan: 01
    provides: "GET /projects/{id}/stats and GET /projects/{id}/activity API endpoints"
  - phase: 03-project-management
    provides: "Project detail page, project members, mini-map"
provides:
  - "StatTile reusable component with icon, label, value, delta display"
  - "ProjectStats 6-column responsive grid with tooltips"
  - "ActivityTimeline with day-grouped vertical timeline and event-type icons"
  - "ProjectActivity client component with load-more cursor pagination"
  - "Restructured project detail page with stats row and activity feed"
  - "Bilingual dashboard i18n keys (EN + BG)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "getFormatter/getNow from next-intl/server for relative time formatting"
    - "Promise.allSettled for parallel optional API fetches with graceful fallback"
    - "Server component renders client tooltip boundary for interactive hover"
    - "Client component wraps server-compatible presentational timeline"

key-files:
  created:
    - "web/src/app/[locale]/projects/_components/stat-tile.tsx"
    - "web/src/app/[locale]/projects/_components/project-stats.tsx"
    - "web/src/app/[locale]/projects/_components/activity-timeline.tsx"
    - "web/src/app/[locale]/projects/_components/project-activity.tsx"
  modified:
    - "web/src/types/project.ts"
    - "web/src/app/[locale]/projects/_actions.ts"
    - "web/src/app/[locale]/projects/[id]/page.tsx"
    - "web/src/messages/en.json"
    - "web/src/messages/bg.json"

key-decisions:
  - "Promise.allSettled for stats/activity fetches -- page renders even if dashboard APIs fail"
  - "Simplified Project Info card to remove duplicate name/status (already shown in header and stat tiles)"
  - "StatTile accepts number | string | null for value -- supports both numeric counts and relative time strings"
  - "TooltipProvider wraps only the Last Sync tile (not all stats) to minimize client boundary"

patterns-established:
  - "getFormatter + getNow for server-side relative time rendering (avoids hydration mismatch)"
  - "Promise.allSettled for graceful optional data fetching alongside required data"

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 4 Plan 02: Stat Tiles & Activity Feed UI Summary

**Six stat tiles (closures, poles, cables, cable length, team size, last sync) in responsive grid plus day-grouped activity timeline with load-more pagination, integrated into restructured project detail page**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-21T23:52:39Z
- **Completed:** 2026-02-21T23:56:51Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- StatTile component renders icon, label, value (with em-dash for null), optional delta indicator with green/red coloring
- ProjectStats grid displays 6 metrics in a responsive 2/3/6-column layout with tooltip on last sync tile showing exact date
- ActivityTimeline groups entries by day (Today, Yesterday, formatted date) with color-coded event icons (blue upload, green assign, red remove, amber status change)
- ProjectActivity client wrapper manages load-more state via fetchActivity server action with cursor-based pagination
- Project detail page restructured: stat tiles row above content grid, activity feed below map in left column
- All new text bilingual (EN + BG) via dashboard i18n namespace

## Task Commits

Each task was committed atomically:

1. **Task 1: Add types, server action, and presentational components** - `dbbf9c1` (feat)
2. **Task 2: Build ProjectStats grid, ProjectActivity client wrapper, and restructure detail page** - `3586871` (feat)

## Files Created/Modified
- `web/src/types/project.ts` - Added ProjectStats, ActivityEntry, ActivityPage types
- `web/src/app/[locale]/projects/_actions.ts` - Added fetchActivity server action with snake_case mapping
- `web/src/app/[locale]/projects/_components/stat-tile.tsx` - Reusable stat card with icon, label, value, delta
- `web/src/app/[locale]/projects/_components/project-stats.tsx` - 6-tile responsive grid with tooltip on last sync
- `web/src/app/[locale]/projects/_components/activity-timeline.tsx` - Vertical timeline with day grouping and event icons
- `web/src/app/[locale]/projects/_components/project-activity.tsx` - Client component with load-more pagination
- `web/src/app/[locale]/projects/[id]/page.tsx` - Restructured layout with stats row and activity feed
- `web/src/messages/en.json` - Added dashboard namespace with 18 keys
- `web/src/messages/bg.json` - Added dashboard namespace with 18 keys

## Decisions Made
- Used Promise.allSettled instead of try/catch for parallel stats/activity fetches -- cleaner code, page renders even if dashboard APIs fail
- Simplified Project Info card by removing name and status fields (already visible in page header and stat tiles) -- keeps description and createdAt only
- StatTile value prop accepts number | string | null to handle both numeric counts and the relative time string for last sync
- TooltipProvider wraps only the Last Sync tile rather than the entire stats grid to minimize client JS boundary
- Used getFormatter/getNow from next-intl/server for server-side relative time rendering to avoid hydration mismatches

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- This completes Phase 4 (Dashboard & Analytics) -- both API and UI plans are done
- All 4 phases of the roadmap are now complete
- Project detail page fully functional with stats, activity feed, map, members, and actions

## Self-Check: PASSED

- All 9 files exist on disk
- Both task commits (dbbf9c1, 3586871) found in git log
- TypeScript compilation passes (npx tsc --noEmit)
- Next.js production build succeeds

---
*Phase: 04-dashboard-analytics*
*Completed: 2026-02-22*

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Users can log in to a unified system (Kanidm), manage projects, and work with fiber optic networks -- from both QGIS and a web browser.
**Current focus:** Phase 4 Dashboard & Analytics

## Current Position

Phase: 4 of 4 (Dashboard & Analytics)
Plan: 2 of 2 in current phase -- 04-02 complete
Status: All phases complete -- stat tiles, activity feed UI integrated into project detail page
Last activity: 2026-02-22 -- Plan 04-02 completed

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 11
- Average duration: 5 min
- Total execution time: 1.1 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3/3 | 24 min | 8 min |
| 02 | 3/3 | 14 min | 5 min |
| 03 | 3/3 | 11 min | 4 min |
| 04 | 2/2 | 7 min | 4 min |

**Recent Trend:**
- Last 5 plans: 03-02 (5 min), 03-03 (4 min), 04-01 (3 min), 04-02 (4 min)
- Trend: stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 4 phases derived from 22 requirements; auth first because all 7 critical pitfalls live there
- [Roadmap]: UIUX-01 and UIUX-02 placed in Phase 1 (shell-level concerns, not feature-level)
- [Phase 1]: Collapsible sidebar navigation, green/teal color scheme, data-dense UI style
- [Phase 1]: Direct Kanidm redirect (no FiberQ landing page), role-based redirect after login
- [Phase 1]: Bilingual interface (BG + EN) from day one
- [Phase 1]: System preference theme (auto dark/light)
- [Phase 1]: MIGRATED from Zitadel to Kanidm -- ES256 JWT, group-based roles with fiberq_ prefix
- [01-01]: Auth.js v5 auth() wrapper for proxy.ts -- cleanest NextAuth session integration
- [01-01]: Green/teal oklch palette with 0.375rem radius for compact data-dense feel
- [01-01]: Fixed root .gitignore lib/ -> /lib/ to avoid ignoring web/src/lib/
- [01-01]: 4 frontend roles (added project_manager) ahead of backend extension in Phase 2
- [01-02]: Collapsible sidebar with collapsible="icon" variant for tablet/desktop, Sheet on mobile
- [01-02]: Providers wrapper: SessionProvider > NextIntlClientProvider > ThemeProvider
- [01-02]: LanguageSwitcher as simple toggle button (not dropdown) -- only 2 locales
- [01-02]: Fixed --sidebar-background to --sidebar to match shadcn/ui theme mapping
- [01-03]: Kanidm OIDC per-client discovery URL pattern
- [01-03]: Simple signOut (no federated logout) -- Kanidm does not expose end_session_endpoint
- [01-03]: Auth.js v5 signin URL must be /api/auth/signin (not /api/auth/signin/kanidm for GET)
- [02-01]: KanidmAdminClient as plain class instantiated per-request via factory function
- [02-01]: INTERNAL_API_URL env var for server-side auth.ts record-login call
- [02-01]: Fire-and-forget login tracking pattern -- never blocks sign-in flow
- [02-02]: Server component fetches + maps snake_case to camelCase, passes to client wrapper for table rendering
- [02-02]: DataTable owns table instance internally, renders toolbar with table ref
- [02-02]: Server Actions return discriminated union { success: true, data: T } | { success: false, error: string }
- [02-02]: Graceful fallback: empty table when API unavailable
- [02-03]: Server Component detail page with extracted UserDetailActions client component for interactive dialogs
- [02-03]: Shared ConfirmActionDialog reused across table dropdown and detail page actions
- [02-03]: stopPropagation on actions column cell to prevent row click navigation with dropdown
- [02-03]: Roles card and actions card in right column sidebar layout on detail page
- [03-01]: Denormalized user_display_name/user_email in project_users to avoid Kanidm lookups
- [03-01]: Batch PostGIS extent via UNION ALL grouped by project_id (avoids N+1)
- [03-01]: assignable-users from user_logins table (pragmatic shortcut, no Kanidm API call)
- [03-01]: Upsert pattern for member assignment (ON CONFLICT DO UPDATE)
- [03-02]: MapLibre GL with inline OSM raster tiles for mini-maps (no external tile server)
- [03-02]: Intersection Observer lazy loading for WebGL context limits with many project cards
- [03-02]: canCreate derived from admin or project_manager role on server side, passed as prop
- [03-03]: ConfirmActionDialog reused from Phase 2 users module for member removal (cross-module import)
- [03-03]: Interactive prop on ProjectMiniMap (default false) -- detail page map has NavigationControl, card maps static
- [03-03]: Lazy-load assignable users via server action when combobox opens (not on page load)
- [03-03]: canManage derived from admin, global project_manager, or project-level manager role
- [04-01]: Stats return null for counts when no completed sync_log entry exists (not 0) -- distinguishes 'no data' from 'zero elements'
- [04-01]: Activity feed skips assignment logging to project_activity_log to avoid duplicate events (assignments queryable from project_users)
- [04-01]: Route ordering: stats and activity endpoints before /{project_id} detail to prevent FastAPI route shadowing
- [04-01]: _check_project_visibility helper extracted for reusable project existence + access checks
- [04-02]: Promise.allSettled for stats/activity fetches -- page renders even if dashboard APIs fail
- [04-02]: StatTile value accepts number | string | null for both numeric counts and relative time
- [04-02]: getFormatter/getNow from next-intl/server for server-side relative time (avoids hydration mismatch)
- [04-02]: Simplified Project Info card -- removed duplicate name/status already visible in header

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1]: Auth.js v5 beta stability -- monitor
- [Phase 1]: Zod 4 + @hookform/resolvers compatibility -- RESOLVED: zod 3.x + @hookform/resolvers installed and working
- [Phase 2]: Kanidm API access for user management -- RESOLVED: using V1 REST API with service account token

## Session Continuity

Last session: 2026-02-22
Stopped at: Completed 04-02-PLAN.md -- All phases complete
Resume file: N/A -- All 4 phases executed

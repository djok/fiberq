# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Users can log in to a unified system (Kanidm), manage projects, and work with fiber optic networks -- from both QGIS and a web browser.
**Current focus:** Phase 2 User Management -- backend API for user CRUD

## Current Position

Phase: 2 of 4 (User Management)
Plan: 1 of 3 in current phase -- 02-01 complete
Status: Plan 02-01 complete -- Kanidm admin API proxy, user CRUD endpoints, login tracking
Last activity: 2026-02-21 -- Plan 02-01 completed

Progress: [████░░░░░░] 33%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 7 min
- Total execution time: 0.5 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3/3 | 24 min | 8 min |
| 02 | 1/3 | 4 min | 4 min |

**Recent Trend:**
- Last 5 plans: 01-01 (9 min), 01-02 (5 min), 01-03 (10 min), 02-01 (4 min)
- Trend: improving

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

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1]: Auth.js v5 beta stability -- monitor
- [Phase 1]: Zod 4 + @hookform/resolvers compatibility -- verify at project setup, fall back to Zod 3.24.x if needed
- [Phase 2]: Kanidm API access for user management -- RESOLVED: using V1 REST API with service account token

## Session Continuity

Last session: 2026-02-21
Stopped at: Completed 02-01-PLAN.md
Resume file: .planning/phases/02-user-management/02-01-SUMMARY.md

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Users can log in to a unified system (Kanidm), manage projects, and work with fiber optic networks -- from both QGIS and a web browser.
**Current focus:** Phase 1 complete, ready for Phase 2

## Current Position

Phase: 1 of 4 (Auth Foundation & App Shell) -- COMPLETE
Plan: 3 of 3 in current phase -- all done
Status: Phase 1 complete -- Kanidm OIDC, app shell, profile, placeholder pages
Last activity: 2026-02-21 -- Kanidm migration + plan 01-03 completed

Progress: [███░░░░░░░] 25%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 8 min
- Total execution time: 0.4 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3/3 | 24 min | 8 min |

**Recent Trend:**
- Last 5 plans: 01-01 (9 min), 01-02 (5 min), 01-03 (10 min)
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

### Pending Todos

None.

### Blockers/Concerns

- [Phase 1]: Auth.js v5 beta stability -- monitor
- [Phase 1]: Zod 4 + @hookform/resolvers compatibility -- verify at project setup, fall back to Zod 3.24.x if needed
- [Phase 2]: Kanidm API access for user management -- need to determine approach (CLI vs API vs SCIM)

## Session Continuity

Last session: 2026-02-21
Stopped at: Phase 2 context gathered
Resume file: .planning/phases/02-user-management/02-CONTEXT.md

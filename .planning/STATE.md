# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-21)

**Core value:** Users can log in to a unified system (Zitadel), manage projects, and work with fiber optic networks -- from both QGIS and a web browser.
**Current focus:** Phase 1: Auth Foundation & App Shell

## Current Position

Phase: 1 of 4 (Auth Foundation & App Shell)
Plan: 2 of 3 in current phase
Status: Plan 01-02 complete -- App shell with sidebar, theming, and i18n
Last activity: 2026-02-21 -- Plan 01-02 executed (5 min)

Progress: [███░░░░░░░] 25%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 7 min
- Total execution time: 0.23 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 2/3 | 14 min | 7 min |

**Recent Trend:**
- Last 5 plans: 01-01 (9 min), 01-02 (5 min)
- Trend: improving

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 4 phases derived from 22 requirements; auth first because all 7 critical pitfalls live there
- [Roadmap]: UIUX-01 and UIUX-02 placed in Phase 1 (shell-level concerns, not feature-level)
- [Phase 1]: Collapsible sidebar navigation, green/teal color scheme, data-dense UI style
- [Phase 1]: Direct Zitadel redirect (no FiberQ landing page), role-based redirect after login
- [Phase 1]: Bilingual interface (BG + EN) from day one
- [Phase 1]: System preference theme (auto dark/light)
- [01-01]: Auth.js v5 auth() wrapper for proxy.ts -- cleanest NextAuth session integration
- [01-01]: Green/teal oklch palette with 0.375rem radius for compact data-dense feel
- [01-01]: Fixed root .gitignore lib/ -> /lib/ to avoid ignoring web/src/lib/
- [01-01]: 4 frontend roles (added project_manager) ahead of backend extension in Phase 2
- [01-02]: Collapsible sidebar with collapsible="icon" variant for tablet/desktop, Sheet on mobile
- [01-02]: Providers wrapper: SessionProvider > NextIntlClientProvider > ThemeProvider
- [01-02]: LanguageSwitcher as simple toggle button (not dropdown) -- only 2 locales
- [01-02]: Fixed --sidebar-background to --sidebar to match shadcn/ui theme mapping

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1]: Auth.js v5 beta stability -- monitor, but Zitadel docs use it as reference implementation
- [Phase 1]: Zod 4 + @hookform/resolvers compatibility -- verify at project setup, fall back to Zod 3.24.x if needed
- [Phase 2]: Zitadel service account provisioning needed for Management API access -- operational prerequisite

## Session Continuity

Last session: 2026-02-21
Stopped at: Completed 01-02-PLAN.md (App shell with sidebar, theming, i18n)
Resume file: .planning/phases/01-auth-foundation-app-shell/01-03-PLAN.md

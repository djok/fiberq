---
phase: 01-auth-foundation-app-shell
plan: 02
subsystem: ui, layout
tags: [shadcn-ui, sidebar, next-themes, next-intl, oklch, responsive, role-based-nav, i18n]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Next.js 16 scaffold, Auth.js config, roles.ts, i18n routing, shadcn/ui sidebar component"
provides:
  - "Authenticated app shell layout with collapsible sidebar"
  - "Role-filtered sidebar navigation using filterNavByRole"
  - "Providers component combining SessionProvider + ThemeProvider + NextIntlClientProvider"
  - "UserNav dropdown with avatar, profile link, sign out"
  - "ThemeToggle (light/dark/system) using next-themes"
  - "LanguageSwitcher (BG/EN) using next-intl locale routing"
  - "Green/teal oklch color palette (light + dark) with data-dense typography"
  - "FiberQ network logo SVG"
  - "Root page role-based redirect (admin -> /users, others -> /projects)"
affects: [01-03, 02-project-management]

# Tech tracking
tech-stack:
  added: []
  patterns: [collapsible icon sidebar with SidebarProvider, role-filtered nav items, Providers wrapper for session+theme+intl, locale-aware navigation with next-intl Link and redirect]

key-files:
  created:
    - web/src/app/[locale]/layout.tsx
    - web/src/app/[locale]/page.tsx
    - web/src/components/providers.tsx
    - web/src/components/app-sidebar.tsx
    - web/src/components/sidebar-nav.tsx
    - web/src/components/user-nav.tsx
    - web/src/components/theme-toggle.tsx
    - web/src/components/language-switcher.tsx
    - web/public/logo.svg
  modified:
    - web/src/app/globals.css
    - web/src/messages/en.json
    - web/src/messages/bg.json

key-decisions:
  - "Used collapsible='icon' sidebar variant for tablet collapse (icons-only) with Sheet on mobile -- shadcn/ui built-in pattern"
  - "Kept sidebar as default variant (not floating/inset) for data-dense professional feel"
  - "Used useTranslations() without namespace for flexible dot-notation key access across nav items"
  - "LanguageSwitcher as simple toggle button (not dropdown) since only 2 locales"

patterns-established:
  - "Providers wrapper: SessionProvider > NextIntlClientProvider > ThemeProvider wrapping all authenticated content"
  - "Sidebar layout: SidebarProvider > AppSidebar + SidebarInset with header bar containing SidebarTrigger, LanguageSwitcher, ThemeToggle"
  - "Role-based nav: SidebarNav receives roles prop, filters via filterNavByRole, renders SidebarMenuButton with tooltip"
  - "UserNav pattern: SidebarFooter with DropdownMenu trigger showing avatar + name, dropdown with profile link and sign out"
  - "group-data-[collapsible=icon]:hidden for hiding text when sidebar collapsed to icons"

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 1 Plan 02: App Shell & Sidebar Summary

**Collapsible sidebar shell with role-filtered navigation, green/teal oklch theming (light+dark), BG/EN language switcher, and system-preference theme toggle**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T15:53:07Z
- **Completed:** 2026-02-21T15:58:17Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- Complete authenticated app shell layout with collapsible sidebar that collapses to icons on tablet (768-1023px), renders as slide-over Sheet on mobile (<768px), and shows full labels on desktop
- Green/teal oklch color palette applied consistently across light and dark modes with data-dense typography (14px base, 1.4 line-height, tabular-nums)
- Role-based navigation filtering: admin sees Dashboard, Projects, Users, Profile; non-admin users do not see Users link
- Theme toggle (light/dark/system) and BG/EN language switcher in the header bar
- Root locale page redirects to role-appropriate default page (admin -> /users, others -> /projects)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create green/teal color palette, data-dense typography, and providers** - `5537678` (feat)
2. **Task 2: Build the collapsible sidebar shell with role-based navigation** - `17407ad` (feat)

## Files Created/Modified

- `web/src/app/globals.css` - Updated oklch color palette (light+dark) with data-dense body typography
- `web/src/components/providers.tsx` - Combined SessionProvider + NextIntlClientProvider + ThemeProvider wrapper
- `web/public/logo.svg` - FiberQ network logo (teal fiber optic node icon)
- `web/src/app/[locale]/layout.tsx` - Authenticated shell layout with SidebarProvider, AppSidebar, header bar
- `web/src/app/[locale]/page.tsx` - Root page with role-based redirect
- `web/src/components/app-sidebar.tsx` - Main sidebar with logo header, nav content, user footer, rail
- `web/src/components/sidebar-nav.tsx` - Role-filtered navigation items with active state highlighting
- `web/src/components/user-nav.tsx` - User avatar dropdown with profile link and sign out action
- `web/src/components/theme-toggle.tsx` - Light/dark/system theme toggle via next-themes
- `web/src/components/language-switcher.tsx` - BG/EN toggle via next-intl locale routing
- `web/src/messages/en.json` - Added nav.navigation i18n key
- `web/src/messages/bg.json` - Added nav.navigation i18n key (Bulgarian)

## Decisions Made

- Used `collapsible="icon"` sidebar variant for seamless tablet/desktop collapse behavior -- this is the shadcn/ui built-in pattern that handles all responsive states
- Kept sidebar as `variant="sidebar"` (not floating/inset) for a clean data-dense professional look matching the CONTEXT.md vision
- Used `useTranslations()` without namespace so nav items can use dot-notation keys like `nav.dashboard` directly
- Implemented LanguageSwitcher as a simple toggle button rather than dropdown, since there are only 2 locales (BG/EN)
- Fixed `--sidebar-background` CSS variable naming to `--sidebar` to match shadcn/ui theme mapping expectations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed sidebar CSS variable naming mismatch**
- **Found during:** Task 1 (color palette update)
- **Issue:** Plan specified `--sidebar-background` but shadcn/ui `@theme inline` maps `--color-sidebar` to `var(--sidebar)` (not `var(--sidebar-background)`)
- **Fix:** Used `--sidebar` instead of `--sidebar-background` in both light and dark mode CSS blocks
- **Files modified:** `web/src/app/globals.css`
- **Verification:** `npm run build` succeeds, sidebar background color resolves correctly
- **Committed in:** 5537678 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** CSS variable naming fix was necessary for sidebar background color to resolve. No scope creep.

## Issues Encountered

None -- all components compiled and built successfully on first attempt.

## User Setup Required

None -- no external service configuration required. This plan builds on the auth foundation from Plan 01.

## Next Phase Readiness

- App shell is complete and ready for Plan 03 (profile page, federated logout, placeholder pages)
- All sidebar navigation links point to routes that will be created in Plan 03 and later phases
- Theme and language infrastructure is in place for all future page content
- Providers wrapper is the single entry point for adding future providers (e.g., query client)

## Self-Check: PASSED

All 12 key files verified present. Both task commits verified in git log.

---
*Phase: 01-auth-foundation-app-shell*
*Completed: 2026-02-21*

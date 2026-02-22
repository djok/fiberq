---
phase: 01-auth-foundation-app-shell
plan: 01
subsystem: auth, infra
tags: [next.js, auth.js, zitadel, oidc, next-intl, shadcn-ui, tailwind-v4, docker, nginx, cors]

# Dependency graph
requires: []
provides:
  - "Next.js 16 project scaffold with App Router, Tailwind v4, shadcn/ui"
  - "Auth.js v5 Zitadel OIDC integration with raw token forwarding"
  - "proxy.ts composing auth-then-i18n for all routes"
  - "API client forwarding raw Zitadel JWT to FastAPI"
  - "Role constants and nav filtering matching backend model"
  - "i18n foundation (en/bg) with next-intl"
  - "Nginx routing /api/auth/ to Next.js, /api/ to FastAPI"
  - "Docker Compose web service with health checks"
  - "CORS fix: explicit origins instead of wildcard"
affects: [01-02, 01-03, 02-auth-api-extensions]

# Tech tracking
tech-stack:
  added: [next.js 16.1.6, next-auth 5.0.0-beta.30, next-intl 4.8.3, next-themes 0.4.6, lucide-react, shadcn/ui, tailwindcss 4.x, tw-animate-css]
  patterns: [auth-then-i18n proxy composition, raw token forwarding, role-based nav filtering, standalone Docker build]

key-files:
  created:
    - web/src/auth.ts
    - web/src/auth.config.ts
    - web/src/proxy.ts
    - web/src/lib/api.ts
    - web/src/lib/roles.ts
    - web/src/i18n/routing.ts
    - web/src/i18n/navigation.ts
    - web/src/i18n/request.ts
    - web/src/messages/en.json
    - web/src/messages/bg.json
    - web/src/types/next-auth.d.ts
    - web/src/app/api/auth/[...nextauth]/route.ts
    - web/Dockerfile
    - web/.env.local
  modified:
    - server/nginx/nginx.conf
    - server/api/main.py
    - server/docker-compose.yml
    - .gitignore

key-decisions:
  - "Used Auth.js v5 auth() wrapper for proxy.ts instead of separate auth check -- simplifies session access"
  - "Green/teal oklch palette with compact radius (0.375rem) for data-dense telecom feel"
  - "Fixed root .gitignore lib/ pattern to /lib/ to avoid ignoring web/src/lib/"
  - "Added project_manager role to frontend constants (4 roles) matching PROJECT.md decision, ahead of backend extension"

patterns-established:
  - "Auth-then-i18n: proxy.ts checks auth BEFORE running intlMiddleware to prevent redirect loops"
  - "Raw token forwarding: session.accessToken is always the Zitadel JWT, never the NextAuth JWE"
  - "Role extraction: decodeJwtPayload + extractRolesFromClaims matching backend _extract_roles() logic"
  - "API client pattern: apiFetch() uses auth() to get session, forwards Bearer token"
  - "Green/teal color scheme: oklch-based CSS variables with light/dark mode support"

# Metrics
duration: 9min
completed: 2026-02-21
---

# Phase 1 Plan 01: Next.js + Auth.js + Zitadel Foundation Summary

**Next.js 16 with Auth.js v5 Zitadel OIDC, raw JWT forwarding, auth-then-i18n proxy, and Docker/Nginx infrastructure integration**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-21T15:40:07Z
- **Completed:** 2026-02-21T15:49:26Z
- **Tasks:** 3
- **Files modified:** 45

## Accomplishments

- Next.js 16.1.6 project with Turbopack, Tailwind v4 (CSS-first), shadcn/ui components (sidebar, button, avatar, dropdown-menu, etc.), and standalone Docker build
- Auth.js v5 fully configured with Zitadel OIDC provider including PKCE, offline_access scope for silent refresh, and role claim extraction matching the existing FastAPI backend pattern
- proxy.ts composing auth check then i18n routing, preventing redirect loops for unauthenticated users
- Infrastructure updated: Nginx routes /api/auth/ to Next.js and /api/ to FastAPI; CORS fixed with explicit origins; Docker Compose web service added with health checks
- i18n foundation with next-intl for Bulgarian and English, translation files with all UI strings

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Next.js 16 project with all dependencies and core configuration** - `449309d` (feat)
2. **Task 2: Configure Auth.js with Zitadel, proxy.ts, API client, and roles** - `07fc0c4` (feat)
3. **Task 3: Update infrastructure -- Nginx, CORS fix, Docker Compose web service** - `f76b0f6` (feat)

## Files Created/Modified

- `web/src/auth.ts` - Auth.js v5 with Zitadel provider, JWT/session callbacks, token refresh
- `web/src/auth.config.ts` - Edge-compatible auth config for proxy.ts
- `web/src/proxy.ts` - Auth-then-i18n proxy composition
- `web/src/lib/api.ts` - Server-side fetch helper forwarding raw Zitadel JWT
- `web/src/lib/roles.ts` - Role constants, nav items, filterNavByRole, getDefaultRedirect
- `web/src/lib/utils.ts` - shadcn/ui cn() utility
- `web/src/i18n/routing.ts` - Locale config (en, bg)
- `web/src/i18n/navigation.ts` - Locale-aware navigation exports
- `web/src/i18n/request.ts` - Server-side locale resolution
- `web/src/messages/en.json` - English translations
- `web/src/messages/bg.json` - Bulgarian translations
- `web/src/types/next-auth.d.ts` - Auth.js type augmentation (accessToken, roles)
- `web/src/app/api/auth/[...nextauth]/route.ts` - NextAuth route handler
- `web/src/app/layout.tsx` - Root layout with FiberQ metadata
- `web/src/app/globals.css` - Green/teal color scheme with light/dark mode
- `web/src/app/page.tsx` - Placeholder page
- `web/next.config.ts` - Standalone output + next-intl plugin
- `web/Dockerfile` - Multi-stage standalone build
- `web/package.json` - All dependencies
- `web/components.json` - shadcn/ui configuration
- `web/src/components/ui/*.tsx` - 10 shadcn/ui components
- `server/nginx/nginx.conf` - Added /api/auth/ routing and web upstream
- `server/api/main.py` - CORS fix with explicit origins
- `server/docker-compose.yml` - Added web service with env vars and health check

## Decisions Made

- Used Auth.js v5 `auth()` wrapper for proxy.ts instead of a separate auth check function -- this provides the cleanest integration with the NextAuth session
- Applied green/teal oklch palette with 0.375rem radius for compact data-dense telecom aesthetic per CONTEXT.md
- Fixed root `.gitignore` pattern `lib/` to `/lib/` (scoped to root) -- the Python packaging pattern was incorrectly ignoring `web/src/lib/`
- Added `project_manager` as the 4th role in frontend constants, ahead of the backend which currently has 3 roles (will be extended in Phase 2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed .gitignore lib/ pattern conflict**
- **Found during:** Task 1 (project scaffolding)
- **Issue:** Root `.gitignore` had `lib/` (Python distribution pattern) which prevented `web/src/lib/utils.ts` and other lib files from being tracked by git
- **Fix:** Changed `lib/` to `/lib/` in root `.gitignore` to scope it to the repo root only
- **Files modified:** `.gitignore`
- **Verification:** `git check-ignore -v web/src/lib/utils.ts` returns no match; file stages correctly
- **Committed in:** 449309d (Task 1 commit)

**2. [Rule 1 - Bug] Fixed TypeScript error in auth.ts expiresAt comparison**
- **Found during:** Task 2 (auth configuration)
- **Issue:** `token.expiresAt` had conflicting type from Auth.js JWT interface, causing `TS2365: Operator '>' cannot be applied` error
- **Fix:** Added explicit type assertion `const expiresAt = token.expiresAt as number | undefined` before comparison
- **Files modified:** `web/src/auth.ts`
- **Verification:** `npx tsc --noEmit` passes with zero errors
- **Committed in:** 07fc0c4 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered

- Next.js `create-next-app` scaffold did not create `src/` directory despite plan expectations -- moved `app/` into `src/` and updated tsconfig paths
- shadcn/ui reported "Circular dependency detected in registry items" during component installation but completed successfully

## User Setup Required

**External services require manual configuration.** The plan's `user_setup` section specifies Zitadel configuration:

1. Create a Web application in the Zitadel project (Console > Project > Applications > New > Web)
2. Copy Client ID to `AUTH_ZITADEL_ID` environment variable
3. Generate and copy Client Secret to `AUTH_ZITADEL_SECRET`
4. Set redirect URI to `http://localhost:3000/api/auth/callback/zitadel` (dev)
5. Set post-logout redirect URI to `http://localhost:3000` (dev)
6. Enable "Assert Roles on Authentication" in Project settings
7. Enable "User Roles Inside ID Token" in Application Token Settings
8. Generate `AUTH_SECRET` with `openssl rand -base64 32`

## Next Phase Readiness

- Auth foundation complete: auth.ts, proxy.ts, api.ts, roles.ts all ready for Plan 02 (app shell layout, profile page, providers)
- shadcn/ui sidebar and all required UI components installed and ready
- i18n routing and translations ready for locale-wrapped layouts
- Infrastructure (Nginx, Docker Compose) ready for deployment once Zitadel is configured

## Self-Check: PASSED

All 17 key files verified present. All 3 task commits verified in git log.

---
*Phase: 01-auth-foundation-app-shell*
*Completed: 2026-02-21*

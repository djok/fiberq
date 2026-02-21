---
phase: 01-auth-foundation-app-shell
plan: 03
subsystem: auth, pages
tags: [kanidm, oidc, profile, logout, placeholder-pages, migration]

# Dependency graph
requires:
  - phase: 01-02
    provides: "App shell layout, sidebar navigation, providers, theming, i18n"
provides:
  - "Profile page with user data (name, email, role, avatar)"
  - "Profile card component with edit link to Kanidm"
  - "Placeholder pages for Dashboard, Projects, Users"
  - "Admin-only access check on Users page"
  - "Simple logout (local session clear)"
  - "Complete Kanidm OIDC integration replacing Zitadel"
  - "Auth.js v5 custom OIDC provider for Kanidm"
  - "Backend token validation against Kanidm JWKS (ES256)"
affects: [02-user-management]

# Tech tracking
tech-stack:
  added: []
  removed: [zitadel]
  replaced: [{from: "next-auth/providers/zitadel", to: "custom OIDC provider for Kanidm"}]
  patterns: [per-client OIDC discovery URL, group-based roles with fiberq_ prefix, ES256 JWT validation, PKCE S256]

key-files:
  created:
    - web/src/app/[locale]/profile/page.tsx
    - web/src/components/profile-card.tsx
    - web/src/app/[locale]/dashboard/page.tsx
    - web/src/app/[locale]/projects/page.tsx
    - web/src/app/[locale]/users/page.tsx
    - server/api/auth/kanidm.py
    - docs/kanidm-setup.md
  modified:
    - web/src/auth.ts
    - web/src/lib/api.ts
    - web/src/components/user-nav.tsx
    - web/src/components/app-sidebar.tsx
    - web/src/proxy.ts
    - web/src/app/[locale]/layout.tsx
    - web/src/app/[locale]/page.tsx
    - web/src/messages/en.json
    - web/src/messages/bg.json
    - web/src/types/next-auth.d.ts
    - server/api/config.py
    - server/api/dependencies.py
  deleted:
    - server/api/auth/zitadel.py
---

## Summary

Plan 01-03 completed Phase 1 with profile page, placeholder pages, and a major identity provider migration from Zitadel to Kanidm.

### What was built

1. **Profile page** (`/[locale]/profile`) — displays name, email, role badges, avatar/initials, last login time, and "Edit Profile" link to Kanidm UI
2. **Placeholder pages** — Dashboard (Phase 4), Projects (Phase 3), Users (Phase 2) with skeleton layouts and coming-soon messages in BG/EN
3. **Admin-only access** — Users page checks `session.user.roles.includes("admin")`
4. **Kanidm OIDC migration** — complete replacement of Zitadel across 18+ files:
   - Frontend: custom OIDC provider in auth.ts with per-client discovery URL
   - Backend: kanidm.py with ES256 JWT validation and group-based role extraction
   - Scopes: `openid profile email groups`
   - Role mapping: Kanidm groups with `fiberq_` prefix stripped to role names
5. **Logout** — simple `signOut({ redirectTo: "/" })` (Kanidm does not expose `end_session_endpoint`)

### Kanidm OIDC specifics

- Discovery URL: `{KANIDM_URL}/oauth2/openid/{client_id}/.well-known/openid-configuration`
- Authorization: `{KANIDM_URL}/ui/oauth2` with PKCE (S256)
- Token signing: ES256 (EdDSA fallback supported)
- Role claim: `groups` array → filter by `fiberq_` prefix → strip prefix

### Commits

- `8ac9f8f` feat(01-03): add profile page and placeholder pages
- `d80f8b8` feat(01-03): implement federated logout
- `7bf2ed4` refactor(auth): migrate identity provider from Zitadel to Kanidm
- `b4c39c9` docs: add Kanidm setup guide for FiberQ
- `238d56e` fix(auth): use generic signin URL for Auth.js v5 compatibility

### Verification

- TypeScript: `npx tsc --noEmit` — no errors
- Build: `npm run build` — success, all routes compiled
- OIDC flow tested with curl:
  - Discovery endpoint returns 200
  - Signin page shows "Sign in with Kanidm" button
  - POST signin redirects to Kanidm authorization with PKCE
  - Kanidm authorization endpoint returns 200 (login form)

### Notes for Phase 2

- Kanidm user management requires CLI or SCIM — no Management API like Zitadel had
- Consider wrapping `kanidm` CLI commands in FastAPI endpoints for WebUI user CRUD
- Group management: `kanidm group add-members fiberq_admin <username>`

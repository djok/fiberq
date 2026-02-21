# Project Research Summary

**Project:** FiberQ WebUI
**Domain:** FTTX/Fiber Optic Network Management — Admin & Project Management WebUI
**Researched:** 2026-02-21
**Confidence:** HIGH

## Executive Summary

FiberQ WebUI is a browser-based administrative interface layered on top of an existing, production-ready backend (FastAPI + PostgreSQL/PostGIS + Zitadel OIDC). The system already handles GIS data sync (QGIS plugin + QField), JWT-based role authorization, and spatial data storage. The WebUI's job is narrow and well-defined: give admins and project managers a browser interface for user lifecycle management and project assignment — functions that currently require direct access to the Zitadel console or raw API calls. The established expert approach for this domain is a thin Next.js (App Router) frontend acting as a Backend-for-Frontend (BFF): Auth.js handles the OIDC login flow, stores the Zitadel access token server-side in an encrypted session cookie, and forwards it as a Bearer header to FastAPI on every API call. The frontend never touches the database directly and never reimplements business logic that already lives in FastAPI.

The recommended stack is Next.js 16 + Auth.js v5 (next-auth@beta) + shadcn/ui + TanStack Query + React Hook Form + Zod. This combination is verified as the de-facto standard for Next.js admin dashboards in 2025-2026. The only consequential uncertainty is Auth.js v5's "beta" label — but with 30 beta releases and adoption by Zitadel's own documentation examples, it is practically stable for this use case. A secondary risk is the planned role rename (admin/engineer/field_worker → Admin/PM/Designer/Field Worker), which must be executed with a phased migration to avoid breaking the QGIS plugin and existing backend simultaneously.

The most dangerous pitfalls are all concentrated in the authentication integration layer: JWT audience mismatch between the frontend and backend Zitadel applications, CORS wildcard misconfiguration blocking credentialed browser requests, NextAuth JWE tokens being forwarded to FastAPI instead of the original Zitadel access tokens, and role claims silently absent from tokens due to missing Zitadel project/application settings. All seven critical pitfalls identified in research must be addressed in the first phase before any feature work begins. The architecture itself is low-risk — Next.js + FastAPI BFF is a thoroughly documented pattern, and the existing Nginx configuration already has a placeholder for the WebUI.

## Key Findings

### Recommended Stack

The frontend is a thin OIDC client with no database of its own. Next.js 16 with App Router is the clear choice: it supports `output: 'standalone'` for a minimal Docker image, the existing Nginx `location /` block is already configured to proxy to it, and all modern patterns (Server Components, Server Actions, middleware route protection) are App Router-only. Auth.js v5 (next-auth@beta) is the recommended auth library because it has a built-in Zitadel provider — zero custom OIDC plumbing — and Zitadel's own documentation uses it as the Next.js reference implementation.

**Core technologies:**
- **Next.js 16.1.x** (App Router, standalone output) — React framework; Nginx already set up for it, standalone mode produces minimal Docker image
- **Auth.js v5 / next-auth@beta** — OIDC client with built-in Zitadel provider; stores and forwards access tokens server-side
- **TypeScript 5.9.x** — non-negotiable for a multi-role system; catches auth/role bugs at compile time
- **Tailwind CSS 4.x** — CSS-first (no config file), 70% smaller output than v3; pairs with shadcn/ui
- **shadcn/ui** — component system copied into the project via CLI; built on Radix UI + Tailwind; dominant pattern for Next.js admin dashboards
- **TanStack Query 5.90.x** — server state, caching, and mutations; de-facto standard for CRUD-heavy React apps
- **TanStack Table 8.21.x** — headless table with sort, filter, and pagination; wrapped by shadcn/ui Data Table component
- **React Hook Form 7.71.x + Zod 4.3.x** — form management and validation; same Zod schema validates on client and server
- **nuqs 2.8.x** — type-safe URL state for table filters and search; keeps UI state bookmarkable
- **Recharts 3.7.x** — chart library bundled with shadcn/ui chart components

**Compatibility note:** Zod 4 is a major version bump. If `@hookform/resolvers` has compatibility issues with Zod 4, fall back to Zod 3.24.x (battle-tested). Verify at implementation start.

See `.planning/research/STACK.md` for full alternatives analysis and "What NOT to Use" list.

### Expected Features

The MVP (12 P1 features) focuses on the two things that make the WebUI essential: user lifecycle management (without logging into the Zitadel console) and project-to-user assignment (without direct API calls). Everything depends on OIDC login being solid first.

**Must have — v1 launch (P1):**
- Zitadel OIDC login + session management + logout — prerequisite for everything
- User list with role display — admin's primary view
- Create user with role assignment — onboarding without Zitadel console
- Deactivate / reactivate user — user lifecycle management
- Project list — every user's landing page after login
- Create / edit project — PM and Admin workflow
- Assign users to project — connects people to work (requires `project_users` junction table, new API endpoint)
- View project members — who is on which team
- Role-based navigation — different UI per role
- My profile page — self-service identity display
- Responsive layout — must work on tablets for field workers

**Should have — v1.x iterations (P2):**
- Project status field and filtering/search
- Project dashboard with aggregate stats (element counts, sync status, team size)
- Activity feed extending the existing `sync_log` table
- Remove user from project, bulk user assignment
- Password reset trigger, last login indicator
- Standalone assign/change role

**Defer — v2+ (P3):**
- Project area map preview (requires map library integration; aligns with next GIS milestone)
- Export project summary (requires PDF/CSV reporting infrastructure)
- User invitation wizard (UX polish; build atoms first, then compose)
- Email notifications (requires SMTP infrastructure)

**Anti-features (deliberately excluded):**
- Full user profile editing (Zitadel is source of truth; display read-only only)
- Per-project permission matrix (4 fixed roles is sufficient; complexity not justified)
- Real-time collaboration (design work stays in QGIS)
- Built-in chat / notifications / multi-tenancy / Kanban boards

See `.planning/research/FEATURES.md` for the full prioritization matrix and competitor analysis.

### Architecture Approach

Next.js acts as a BFF (Backend-for-Frontend): it handles OIDC with Zitadel via Auth.js, stores the Zitadel access token in an encrypted server-side session cookie, and forwards it as `Authorization: Bearer` on all FastAPI calls. Client components never receive the access token. FastAPI's existing JWT validation (`auth/zitadel.py`) requires zero changes. All business logic stays in FastAPI; Next.js is a rendering and routing layer only.

**Major components:**
1. **Nginx** — reverse proxy; routes `/api/*` to FastAPI, `/` to Next.js (already has the location block); must also route `/auth/*` (Auth.js callbacks) to Next.js, not FastAPI
2. **Next.js WebUI** — OIDC login flow, session management, React Server Components for read, Server Actions for write, middleware for route protection; calls FastAPI internally at `http://api:8000`
3. **Auth.js (next-auth@beta)** — manages OIDC flow with Zitadel, stores Zitadel access token in JWT session, exposes `auth()` for server-side token retrieval
4. **FastAPI (existing, unchanged)** — all business logic, role-based access, data validation; validates tokens via Zitadel JWKS (existing, cached)
5. **PostgreSQL/PostGIS (existing, unchanged)** — only FastAPI touches it
6. **Zitadel (external)** — IdP; WebUI needs a new PKCE application registration; service account needed for user management API calls from FastAPI

**Key patterns:**
- React Server Components for initial data fetch (no client-side loading spinners)
- Server Actions for mutations (`revalidatePath` after writes)
- `(authenticated)/` route group with layout-level auth check
- `lib/api-client.ts` as single token-forwarding entry point to FastAPI
- `lib/types.ts` TypeScript interfaces mirroring FastAPI Pydantic models
- `output: 'standalone'` in `next.config.ts` for Docker

See `.planning/research/ARCHITECTURE.md` for full data flow diagrams and Docker Compose / Nginx configuration.

### Critical Pitfalls

All 7 critical pitfalls are concentrated in authentication integration. They must all be resolved in Phase 1 before any feature work starts.

1. **JWT audience mismatch (CRITICAL)** — When the Next.js Zitadel app and the FastAPI Zitadel app have different client IDs, tokens issued to the frontend will be rejected by the backend with 401. Fix: add `urn:zitadel:iam:org:project:id:{projectId}:aud` scope to the Next.js auth request, or update FastAPI's `validate_token()` to accept multiple audiences. Verify by decoding a frontend-obtained token and confirming FastAPI accepts it.

2. **CORS wildcard + credentials (CRITICAL)** — FastAPI currently uses `allow_origins=["*"]` with `allow_credentials=True`, which browsers block for credentialed requests. Fix: replace wildcard with explicit origins (production domain + `http://localhost:3000`). Fix this before any browser testing.

3. **NextAuth JWE forwarded to FastAPI instead of Zitadel JWT (CRITICAL)** — Auth.js session tokens are JWE-encrypted and cannot be validated by FastAPI. Fix: in the `jwt` callback, store `account.access_token` (the Zitadel JWT); in the `session` callback, expose it as `session.accessToken`. Always forward `session.accessToken` to FastAPI, never the Auth.js session token itself.

4. **Zitadel role claims missing from tokens (CRITICAL)** — Three independent settings must ALL be enabled: request scope `urn:zitadel:iam:org:project:roles` in the OIDC flow, enable "Assert Roles on Authentication" in Zitadel project settings, enable "User Roles Inside ID Token" in application settings. Missing any one causes silent role absence and 403 errors everywhere. Write an integration test before building role-gated UI.

5. **Role rename breaks QGIS plugin and backend simultaneously (HIGH)** — Renaming roles in Zitadel (e.g., `engineer` → `PM/Designer`) without a phased migration will break the existing QGIS plugin and all backend role checks at once. Fix: add a normalization mapping in `_extract_roles()` that accepts both old and new role names during the transition window, deploy both old and new roles simultaneously, then remove old roles only after all clients are updated.

6. **NextAuth route conflict with Nginx /api/ prefix (HIGH)** — Auth.js callbacks default to `/api/auth/callback/zitadel`, which matches the existing `/api/` Nginx location block and gets routed to FastAPI (404). Fix: set `basePath: "/auth"` in Auth.js config to move callbacks out of `/api/`, then update the Zitadel redirect URI and Nginx location blocks accordingly.

7. **CVE-2025-29927 — Next.js middleware bypass (HIGH)** — Middleware can be bypassed by setting `x-middleware-subrequest` header. Strip this header in Nginx. Never rely on middleware as the sole security layer — FastAPI's `Depends(require_role)` is the actual security boundary.

See `.planning/research/PITFALLS.md` for recovery strategies, technical debt patterns, and the full "looks done but isn't" checklist.

## Implications for Roadmap

The research strongly implies a 4-phase structure. All 7 critical pitfalls map to Phase 1, and the feature dependency graph shows authentication as the root dependency for everything else.

### Phase 1: Auth Foundation and Infrastructure
**Rationale:** Every feature requires authentication. All 7 critical pitfalls live here. Nothing else can be tested or built correctly until tokens flow properly from browser through Next.js to FastAPI. This phase is also low-feature-count but high-risk — getting it right is the entire point.
**Delivers:** Working OIDC login/logout, session management, token forwarding to FastAPI, role claims verified in tokens, middleware route protection, Docker integration (Dockerfile + Compose + Nginx update), CORS fix in FastAPI.
**Addresses (P1 features):** OIDC login, session management, role-based navigation skeleton, my profile page, responsive layout shell.
**Avoids:** All 7 pitfalls — audience mismatch, CORS wildcard, JWE confusion, missing roles, Nginx routing conflict, SSR token access, middleware bypass CVE.
**Verification gates (from PITFALLS.md):** Decode a frontend token and confirm FastAPI accepts it; call `/auth/me` from a browser on the production domain; call `/auth/roles` and confirm role array matches Zitadel assignment; hard-refresh a protected page and confirm SSR renders with data, not 401.
**Research flag:** Needs `/gsd:research-phase` during planning — the Auth.js + Zitadel + FastAPI integration has multiple coordination points (PKCE app registration, audience scope, service account setup) that benefit from a detailed task checklist.

### Phase 2: User Management
**Rationale:** User management (create, deactivate, assign roles) is the primary reason admins need a WebUI at all. It depends on Phase 1 for authentication and requires a FastAPI service account to call Zitadel Management API. The role rename migration (if executed) must happen in this phase under the normalization mapping added in Phase 1.
**Delivers:** User list with roles, create user with Zitadel invitation flow, deactivate/reactivate user, assign/change role, password reset trigger, last login indicator.
**Uses:** Auth.js session for token forwarding, TanStack Query for user list with cache invalidation, React Hook Form + Zod for create user form, shadcn/ui DataTable with TanStack Table.
**Avoids:** Role rename breakage (phased migration with `ROLE_ALIASES` mapping in backend).
**Research flag:** Zitadel Management API endpoints for user creation, role grant assignment, and user deactivation need to be verified at implementation time. The FastAPI service account setup is an operational step not covered in the tech stack.

### Phase 3: Project Management
**Rationale:** Project CRUD already exists in FastAPI, but the `project_users` junction table (connecting users to projects) does not exist yet. This is the second P1 cluster and depends on Phase 2 having a working user list (you need users before you can assign them to projects).
**Delivers:** Project list (filtered by user assignment for non-admins), create/edit project, project status field, assign users to project (new `project_users` table + API endpoint), view project members, remove user from project, bulk user assignment, project filtering and search.
**Implements:** `project_users` junction table in FastAPI/PostgreSQL; filtered `/projects` endpoint respecting user assignment; nuqs for URL-based filter/search state.
**Research flag:** Standard patterns — TanStack Query mutations + Server Actions for CRUD, TanStack Table for lists. No research needed.

### Phase 4: Dashboard and Analytics
**Rationale:** The dashboard requires both user and project data to be meaningful. Stats (element counts, team size, sync status) aggregate over existing tables (`ftth_okna`, `ftth_stubovi`, `ftth_kablovi_*`, `work_orders`, `sync_log`). This phase adds value without new schema work — it is computed views over existing data. Activity feed extends the existing `sync_log` table.
**Delivers:** Per-project stats dashboard (element counts, team size, last sync), activity feed / audit log, project area map preview (if map library is in scope).
**Uses:** Recharts via shadcn/ui chart components, TanStack Query for prefetched stats, potential Leaflet/MapLibre for map preview (deferred to v2 if scope is tight).
**Research flag:** Dashboard stats queries (aggregate COUNT over ftth_* tables by project_id) need FastAPI endpoint design. Map preview (Leaflet/MapLibre with bounds_geom from PostGIS) may need research if added to this phase.

### Phase Ordering Rationale

- **Auth first:** All 7 critical pitfalls are in Phase 1. Solving them before writing any feature code prevents architectural rework later. The "looks done but isn't" checklist items (token refresh, federated logout, SSR token availability, CORS in staging) all belong to Phase 1 verification.
- **User management before project management:** The `project_users` assignment UI is meaningless without a working user list. Creating users in Phase 2 means Phase 3 has real users to assign.
- **Projects before dashboard:** Stats and activity feeds are aggregate views over project and sync data. Building the underlying entities first ensures the dashboard displays real data immediately.
- **Role rename as part of Phase 2:** The normalization mapping (`ROLE_ALIASES`) is added to the FastAPI backend in Phase 1 (as a pitfall prevention measure). The actual Zitadel role cutover — creating new roles, assigning users, deprecating old roles — happens during Phase 2 User Management, coordinated with the QGIS plugin team.

### Research Flags

**Needs `/gsd:research-phase` during planning:**
- **Phase 1:** Zitadel WebUI app registration steps (PKCE, redirect URIs, project role assertion settings), Auth.js v5 Zitadel provider configuration, FastAPI audience validation modification — multiple coordination points with high coupling.
- **Phase 2:** Zitadel Management API endpoints for user create, role grant, deactivate/reactivate; FastAPI service account setup; invitation email flow.

**Standard patterns (skip research-phase):**
- **Phase 3:** TanStack Query mutations, TanStack Table CRUD, nuqs URL state — thoroughly documented, established patterns.
- **Phase 4:** shadcn/ui chart components with Recharts — well-documented, minimal integration work. Exception: if map preview is added, MapLibre/Leaflet integration needs brief research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via `npm view` on 2026-02-21. Auth.js v5 is "beta" but practically stable with 30 releases and Zitadel's own documentation using it. One LOW-confidence item: Zod 4 + @hookform/resolvers compatibility — needs testing at implementation start. |
| Features | MEDIUM-HIGH | P1 features are well-defined based on domain analysis and existing API. P2 features have clear rationale but their exact API surface depends on FastAPI endpoint additions not yet designed. Competitor analysis is MEDIUM confidence (marketing material). |
| Architecture | HIGH | BFF pattern with Auth.js is verified against official Zitadel docs, Next.js docs, and the existing codebase. All configuration examples cross-checked against actual `server/api/auth/zitadel.py`, `server/nginx/nginx.conf`, and `server/docker-compose.yml`. |
| Pitfalls | HIGH | All 7 critical pitfalls verified against official docs and direct codebase inspection. CVE-2025-29927 is a documented, public vulnerability. Recovery costs and strategies are realistic. |

**Overall confidence:** HIGH

### Gaps to Address

- **Zod 4 + @hookform/resolvers:** Compatibility is unverified. Validate at project setup. If broken, pin to Zod 3.24.x — no architectural impact.
- **FastAPI audience validation change:** The exact modification needed to `server/api/auth/zitadel.py` to accept the WebUI's Zitadel client ID depends on which audience approach is chosen (Option A: multi-audience list; Option B: shared client ID). Decide and implement in Phase 1 before any feature work.
- **Zitadel service account provisioning:** User management from the WebUI requires a Zitadel service account with Management API access. This is an operational prerequisite for Phase 2, not a code change. Must be coordinated with Zitadel admin access.
- **`project_users` junction table schema:** The exact schema (fields, indexes, FK constraints) needs to be designed in Phase 3. The research identifies the need but not the full design.
- **Auth.js v5 long-term maintenance:** The Auth.js + Better Auth merger (Sept 2025) introduces uncertainty about the v5 roadmap. For a project of this scale (tens of users), the beta is stable enough. Monitor merger progress; migration path to Better Auth exists if needed.
- **Role rename timing:** The QGIS plugin team must be informed before any Zitadel role changes. The normalization mapping in FastAPI provides a safe transition window, but operational coordination is required.

## Sources

### Primary (HIGH confidence)
- npm registry (direct `npm view` queries, 2026-02-21) — all package versions
- https://authjs.dev/getting-started/providers/zitadel — Auth.js Zitadel provider
- https://authjs.dev/guides/integrating-third-party-backends — token forwarding pattern
- https://zitadel.com/docs/sdk-examples/nextjs — Zitadel's Next.js reference implementation
- https://zitadel.com/docs/guides/integrate/retrieve-user-roles — role scopes and project settings
- https://zitadel.com/docs/apis/openidoauth/scopes — exact scope strings
- https://zitadel.com/docs/guides/integrate/login/oidc/oauth-recommended-flows — PKCE for web apps
- https://nextjs.org/blog/next-16 — Next.js 16 release, proxy.ts rename
- https://nextjs.org/docs/app/guides/backend-for-frontend — official BFF pattern
- https://fastapi.tiangolo.com/tutorial/cors/ — wildcard + credentials restriction
- https://securitylabs.datadoghq.com/articles/nextjs-middleware-auth-bypass/ — CVE-2025-29927
- Existing codebase: `server/api/auth/zitadel.py`, `server/api/main.py`, `server/nginx/nginx.conf`, `server/docker-compose.yml` — direct inspection

### Secondary (MEDIUM confidence)
- https://www.better-auth.com/blog/authjs-joins-better-auth — Auth.js merger context
- https://github.com/Kiranism/next-shadcn-dashboard-starter — Next.js 16 + shadcn dashboard reference
- https://ui.shadcn.com/docs/installation/next — shadcn/ui Next.js installation
- https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr — TanStack Query SSR
- https://nuqs.dev — nuqs official site
- Procore admin documentation — feature comparison baseline
- IQGeo and VETRO FiberMap product pages — competitor analysis

### Tertiary (LOW confidence)
- Auth.js v5 production stability claims — community reports, no official stable release
- FTTH/FTTX industry trends — vendor blogs

---
*Research completed: 2026-02-21*
*Ready for roadmap: yes*

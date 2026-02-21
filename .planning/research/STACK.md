# Stack Research

**Domain:** FTTX/Fiber Optic Network Management WebUI (Admin + Project Management)
**Researched:** 2026-02-21
**Confidence:** HIGH

## Existing System (Not Researched -- Already Built)

The WebUI integrates with an existing stack:

- **FastAPI** backend at `/api/` behind Nginx reverse proxy
- **PostgreSQL 16 + PostGIS 3.4** database
- **Zitadel OIDC** for identity -- JWT validation with RS256, roles in `urn:zitadel:iam:org:project:roles` claim
- **Docker Compose** deployment with Nginx + Cloudflare Tunnel
- Backend already validates Bearer tokens and extracts roles (admin, engineer, field_worker)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 16.1.x | React framework with App Router, SSR, server components | Current stable (16.1.6 as of Feb 2026). App Router is mature. Standalone output mode produces minimal Docker images. Nginx config already has `location /` prepared for it. |
| React | 19.x | UI library | Ships with Next.js 16. Required peer dependency. |
| TypeScript | 5.9.x | Type safety | Non-negotiable for a multi-role admin system. Catches auth/role bugs at compile time. |
| Tailwind CSS | 4.x | Utility-first styling | v4 is CSS-first (no config file needed), 70% smaller output than v3, 5x faster builds. Pairs with shadcn/ui. |
| Auth.js (next-auth) | 5.0.0-beta.30 | OIDC client for Zitadel | See detailed rationale below. |

**Confidence:** HIGH -- all versions verified via `npm view` on 2026-02-21.

### Auth Library Decision: Auth.js v5 Beta (next-auth@beta)

This is the most consequential stack decision. Three options were evaluated:

**Chosen: Auth.js v5 (next-auth@beta, 5.0.0-beta.30)**

Rationale:
- Has a built-in Zitadel provider (`next-auth/providers/zitadel`) -- zero custom OIDC plumbing.
- Zitadel's own documentation and example repos use Auth.js: https://zitadel.com/docs/sdk-examples/nextjs
- Supports the exact pattern we need: OIDC login with Zitadel, store `access_token` in session, forward as `Authorization: Bearer` header to FastAPI.
- JWT session strategy (no database needed on the frontend side).
- The `jwt` callback captures `account.access_token`, the `session` callback exposes it. Route Handlers forward it to FastAPI. This is documented: https://authjs.dev/guides/integrating-third-party-backends
- Despite "beta" label, v5 has been in production use since 2024. The beta has 30 releases. Auth.js docs default to v5 patterns. The old v4 docs are legacy.
- Auth.js is now maintained by Better Auth Inc. (as of Sept 2025), with security patches continuing.

**Rejected: Better Auth (v1.4.x)**

- Better Auth is designed to own session lifecycle and manage users in its own database. Our architecture has Zitadel as the IdP and FastAPI as the session-of-record backend.
- Adding a Better Auth database for sessions creates redundancy and complexity.
- No built-in Zitadel provider -- would require generic OAuth plugin configuration.
- Better Auth is the right choice when you want the auth library to BE the auth system. Wrong choice when you already have an external IdP (Zitadel) and backend (FastAPI).
- The recommendation to use Better Auth for "new projects" assumes greenfield auth. We are brownfield (Zitadel already deployed).

**Rejected: next-auth v4 (4.24.13 stable)**

- v4 does not support Next.js App Router natively (no `auth()` export, requires `getServerSession` workarounds).
- No `proxy.ts` support (Next.js 16 renamed middleware to proxy).
- v4 is effectively legacy now that Auth.js docs default to v5.

**Confidence:** MEDIUM -- Auth.js v5 is technically "beta" but practically stable. The ecosystem transition to Better Auth introduces uncertainty about long-term maintenance, but for token-forwarding to an existing backend, the v5 beta is the simplest and most proven path. Flag for validation: monitor Auth.js/Better Auth merger progress.

### UI Component System

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| shadcn/ui | latest (CLI-installed) | Component library | Not an npm package -- components are copied into your project via CLI (`npx shadcn@latest add`). Built on Radix UI + Tailwind CSS. Full control over component code. The dominant choice for Next.js admin dashboards in 2025-2026. Compatible with Next.js 16 + React 19. |
| Radix UI | 1.4.x (unified package) | Accessible UI primitives | As of Feb 2026, Radix ships as a single `radix-ui` package instead of many `@radix-ui/react-*` packages. shadcn/ui depends on it. |
| Lucide React | 0.575.x | Icon library | Default icon set for shadcn/ui. Tree-shakeable, consistent design. |
| class-variance-authority | 0.7.x | Variant styling | Used by shadcn/ui for component variants (size, color, state). |
| clsx + tailwind-merge | 2.1.x / 3.5.x | Class name utilities | `cn()` helper function combining clsx + tailwind-merge. Standard shadcn/ui pattern. |

**Confidence:** HIGH -- shadcn/ui is the clear ecosystem standard. Verified compatibility with Next.js 16 via multiple production templates (Kiranism/next-shadcn-dashboard-starter).

### Data Fetching and State

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| TanStack Query | 5.90.x (`@tanstack/react-query`) | Server state management, caching | De facto standard for async data in React. Handles caching, background refetch, optimistic updates, mutation invalidation. Supports SSR hydration with Next.js App Router. As of v5.40.0, supports streaming dehydrated queries. |
| TanStack Table | 8.21.x (`@tanstack/react-table`) | Headless data tables | Required for user and project management tables. Supports sorting, filtering, pagination, column visibility. shadcn/ui provides a pre-built Data Table component wrapping TanStack Table. |
| nuqs | 2.8.x | URL search params state | Type-safe URL state management for table filters, pagination, search. Keeps UI state in URL (shareable, bookmarkable). Used by Sentry, Supabase, Vercel. Only 6 kB gzipped. |

**Confidence:** HIGH -- TanStack Query and Table are verified as the ecosystem standard. nuqs verified via npm (2.8.8) and InfoQ coverage from React Advanced 2025.

### Form Handling and Validation

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| React Hook Form | 7.71.x | Form state management | Lightweight, performant. Uncontrolled components by default (fewer re-renders). Works with Server Actions. |
| Zod | 4.3.x | Schema validation | TypeScript-first. Same schema validates on client (React Hook Form) and server (API route / Server Action). Shared validation = single source of truth. |
| @hookform/resolvers | 5.2.x | RHF + Zod bridge | Connects Zod schemas to React Hook Form validation. |

**Confidence:** HIGH -- React Hook Form + Zod is the established pattern. Versions verified via npm.

### Dashboard and Visualization

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Recharts | 3.7.x | Charts for dashboard | shadcn/ui chart components use Recharts under the hood. Simple API, React-native, responsive. Sufficient for admin dashboard metrics (project counts, user activity). |

**Confidence:** HIGH -- Recharts is bundled with shadcn/ui chart components.

### Development Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| ESLint | 10.x | Linting | Flat config format in v10. Ships with `create-next-app`. |
| Prettier | latest | Code formatting | Pair with `prettier-plugin-tailwindcss` for class sorting. |
| @tailwindcss/postcss | 4.x | PostCSS plugin | Required for Tailwind v4 with Next.js. Replaces the old `tailwindcss` PostCSS plugin. |

**Confidence:** HIGH -- standard tooling.

## Installation

```bash
# Scaffold Next.js 16 project
npx create-next-app@latest webui --typescript --tailwind --eslint --app --src-dir

# Auth
npm install next-auth@beta

# UI (shadcn/ui is installed via CLI, not npm)
npx shadcn@latest init
npx shadcn@latest add button card input label table dialog dropdown-menu select badge separator avatar sheet sidebar command toast tabs form chart

# Data fetching and state
npm install @tanstack/react-query @tanstack/react-table nuqs

# Forms and validation
npm install react-hook-form zod @hookform/resolvers

# Utilities (installed by shadcn CLI, but listed for clarity)
npm install class-variance-authority clsx tailwind-merge lucide-react

# Date handling
npm install date-fns

# Dev dependencies
npm install -D prettier prettier-plugin-tailwindcss
```

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| Auth | Auth.js v5 (next-auth@beta) | Better Auth 1.4.x | When building a NEW auth system without an existing IdP. Better Auth wants to own the user/session lifecycle. Not suitable when Zitadel already owns identity. |
| Auth | Auth.js v5 (next-auth@beta) | arctic + oslo (lightweight OIDC) | When you need minimal OIDC with zero abstraction. More work but fewer opinions. Consider if Auth.js v5 beta instability becomes a real problem. |
| UI | shadcn/ui | Ant Design / MUI | When you need a full pre-built admin theme with less customization work. But you lose Tailwind integration and component ownership. |
| Tables | TanStack Table | AG Grid | When you need Excel-like features (cell editing, pivoting, 100k+ rows). Overkill for user/project management CRUD tables. |
| State | TanStack Query | SWR | SWR is simpler but lacks mutation management, devtools, and the prefetching patterns TanStack Query offers. TanStack Query is better for CRUD-heavy apps. |
| Forms | React Hook Form + Zod | Conform | Conform is server-first and works without JS. Consider if progressive enhancement matters more than DX. |
| Charts | Recharts | Chart.js / D3 | Chart.js for canvas rendering (large datasets). D3 for fully custom visualizations. Recharts is enough for dashboard KPIs. |
| URL State | nuqs | Manual `useSearchParams` | nuqs adds type safety and parsing. Manual approach works for simple cases but gets messy with multiple filter params. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Redux / Zustand for server data | TanStack Query handles server state (fetching, caching, mutations). Adding Redux for API data is redundant complexity. | TanStack Query for server state. Zustand only if you need complex client-only state (unlikely for this project). |
| Axios | fetch() is built into Next.js with caching semantics. Axios adds bundle weight and loses Next.js fetch integration. | Native `fetch()` wrapped in TanStack Query. |
| CSS Modules / Styled Components | Tailwind CSS v4 is already configured. Mixing styling paradigms creates inconsistency and bloats the bundle. | Tailwind CSS utility classes via shadcn/ui components. |
| Prisma / Drizzle (frontend DB) | The frontend does NOT own a database. All data goes through FastAPI. Adding an ORM on the frontend is architectural confusion. | Fetch from FastAPI via TanStack Query. |
| next-auth v4 (stable) | Does not support App Router natively. No `auth()` export. Incompatible with Next.js 16 `proxy.ts`. | next-auth@beta (v5). |
| Custom OIDC implementation | Auth.js v5 has a Zitadel provider that handles PKCE, token refresh, JWKS validation. Rolling your own is error-prone and unnecessary. | Auth.js v5 with Zitadel provider. |
| Pages Router | App Router is the default and future of Next.js. Pages Router is legacy. All new patterns (Server Components, Server Actions, `proxy.ts`) are App Router only. | App Router exclusively. |

## Stack Patterns by Variant

**For user management (Admin CRUD via Zitadel Management API):**
- Use a FastAPI service-account endpoint that calls Zitadel Management API server-side
- Do NOT call Zitadel Management API from the frontend directly
- The frontend calls FastAPI -> FastAPI calls Zitadel Management API with a service account token
- Because: Zitadel Management API requires a service account PAT/client-credentials, which must not be exposed to the browser

**For project management (CRUD via FastAPI):**
- Standard TanStack Query mutations calling FastAPI endpoints
- Optimistic updates for better UX on assign/unassign operations
- nuqs for table filtering/sorting state in URL

**For role-based UI rendering:**
- Extract roles from Auth.js session (originally from Zitadel JWT claims)
- Zitadel scopes needed: `urn:zitadel:iam:org:projects:roles` (to include role claims in token)
- Zitadel console setting: enable "User Roles Inside ID Token" in application settings
- Use React context + hook (`useCurrentUser`) for role-aware component rendering

**For deployment:**
- `output: 'standalone'` in `next.config.ts` for minimal Docker image
- Multi-stage Dockerfile: build stage + runtime stage (node:22-alpine)
- Add `webui` service to existing `docker-compose.yml`
- Update `nginx.conf`: proxy `/` to webui container (port 3000), keep `/api/` proxying to FastAPI

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| next@16.1.x | react@19.x, react-dom@19.x | React 19 is required for Next.js 16. |
| next-auth@5.0.0-beta.30 | next@16.1.x | Auth.js v5 supports App Router and `proxy.ts`. Install as `next-auth@beta`. |
| shadcn/ui | next@16.x, tailwindcss@4.x, radix-ui@1.4.x | shadcn/ui init detects Tailwind v4 and configures accordingly. |
| @tanstack/react-query@5.90.x | react@19.x | Full React 19 support confirmed. |
| @tanstack/react-table@8.21.x | react@19.x | Headless -- no UI dependency conflicts. |
| tailwindcss@4.x | postcss, @tailwindcss/postcss | v4 uses `@import "tailwindcss"` in CSS, not `@tailwind` directives. No `tailwind.config.js` needed. |
| nuqs@2.8.x | next@16.x | Framework-agnostic adapters. Next.js App Router adapter included. |
| zod@4.3.x | typescript@5.9.x | Zod 4.x is a major rewrite with better performance. Verify `@hookform/resolvers` compatibility with Zod 4 at implementation time. |

**Potential compatibility concern:** Zod 4 is relatively new (major version bump). If `@hookform/resolvers` has issues with Zod 4, pin to Zod 3.x (3.24.x) which is battle-tested. **Confidence: LOW** -- needs validation during implementation.

## Key Architecture Decisions Implied by Stack

1. **Frontend is a thin OIDC client** -- Auth.js handles login, session, token storage. FastAPI remains the authority for all business logic and data.
2. **No frontend database** -- all state lives in FastAPI/PostgreSQL. Frontend caches via TanStack Query.
3. **User management routes through FastAPI** -- frontend calls FastAPI admin endpoints, which call Zitadel Management API server-side with a service account.
4. **Standalone Docker deployment** -- Next.js standalone output produces a ~50MB image. Added to existing Docker Compose alongside api/nginx/postgis.

## Sources

### Verified (HIGH confidence)
- npm registry (direct `npm view` queries, 2026-02-21) -- all version numbers
- https://nextjs.org/blog/next-16 -- Next.js 16 release, proxy.ts rename
- https://authjs.dev/getting-started/providers/zitadel -- Auth.js Zitadel provider
- https://authjs.dev/guides/integrating-third-party-backends -- Token forwarding pattern
- https://zitadel.com/docs/sdk-examples/nextjs -- Zitadel's own Next.js guide using Auth.js
- https://zitadel.com/docs/guides/integrate/retrieve-user-roles -- Role claims and scopes
- https://zitadel.com/docs/apis/introduction -- Zitadel Management API (REST + gRPC)
- https://ui.shadcn.com/docs/installation/next -- shadcn/ui Next.js installation
- https://tanstack.com/query/latest/docs/framework/react/guides/advanced-ssr -- TanStack Query SSR

### Verified (MEDIUM confidence)
- https://www.better-auth.com/blog/authjs-joins-better-auth -- Auth.js merger (Sept 2025)
- https://nuqs.dev -- nuqs official site
- https://github.com/Kiranism/next-shadcn-dashboard-starter -- Dashboard template (Next.js 16 + shadcn)

### Consulted (LOW confidence -- training data supplemented)
- Auth.js v5 beta stability claims -- widely used in production per community reports, but no official "stable" release
- Zod 4 + @hookform/resolvers compatibility -- not verified, needs testing

---
*Stack research for: FiberQ WebUI (FTTX Network Management)*
*Researched: 2026-02-21*

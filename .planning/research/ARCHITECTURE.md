# Architecture Research

**Domain:** FTTX/fiber optic network management WebUI (Next.js frontend for existing FastAPI backend)
**Researched:** 2026-02-21
**Confidence:** HIGH

## System Overview

### Current System (Before WebUI)

```
                  Internet
                     |
             Cloudflare Tunnel
                     |
                   Nginx (:80)
                  /     \
          /api/*         /storage/photos/*
            |                  |
      FastAPI (:8000)    Static files (volume)
            |
   PostgreSQL/PostGIS (:5432)
            |
     [fiberq schema]
```

Clients today: QGIS plugin (desktop) + QField (mobile) syncing GeoPackages.
The Nginx config already has a placeholder `location /` block pointing at `/usr/share/nginx/html` for a future WebUI.

### Target System (With WebUI)

```
                  Internet
                     |
             Cloudflare Tunnel
                     |
                   Nginx (:80)
              /    |         \
         /        /api/*      /storage/photos/*
         |         |                |
   Next.js (:3000) FastAPI (:8000) Static files
         |         |
         |    PostgreSQL/PostGIS
         |         |
         +--- Bearer token ---> FastAPI validates JWT
         |
    Zitadel (external OIDC provider)
```

The WebUI is a **thin frontend** that authenticates users via Zitadel OIDC and calls the existing FastAPI endpoints. It does NOT access the database directly. All data flows through the existing REST API.

## Component Boundaries

| Component | Responsibility | Communicates With | Does NOT |
|-----------|---------------|-------------------|----------|
| **Nginx** | Reverse proxy, routing, static file serving | Next.js, FastAPI, photo volume | Touch auth, business logic |
| **Next.js (WebUI)** | User interface, OIDC login flow, session management, client-side state | Zitadel (OIDC), FastAPI (via Bearer token) | Access database directly |
| **FastAPI (API)** | Business logic, data validation, JWT verification, CRUD, sync | PostgreSQL/PostGIS, Zitadel JWKS endpoint | Serve UI, manage sessions |
| **PostgreSQL/PostGIS** | Data persistence, spatial queries | Only FastAPI | Nothing external |
| **Zitadel** | Identity provider, user management, role assignment | Next.js (OIDC flow), FastAPI (JWKS for verification) | Store app data |
| **Cloudflare Tunnel** | Ingress, TLS termination, DDoS protection | Nginx only | Application logic |

### Why Next.js Does NOT Access the Database

The existing FastAPI already has all business logic, role-based access control, and data validation. Making Next.js a second database client would:
- Duplicate authorization logic (currently in FastAPI's `auth/roles.py`)
- Create two sources of truth for validation rules
- Require a Node.js PostGIS driver (unnecessary complexity)
- Break the clean separation where QGIS/QField and WebUI share the same API

The WebUI is a **consumer of the API**, not a peer.

## Recommended Architecture: Next.js as BFF (Backend-for-Frontend)

### Pattern: Auth.js + Server-Side Token Forwarding

Next.js uses Auth.js (NextAuth v5) to handle the Zitadel OIDC flow. The Zitadel access token is stored in an encrypted session cookie. When the WebUI needs data, it makes server-side fetch calls to FastAPI with the access token as a Bearer header. Client components use React hooks that call Next.js API route handlers, which then forward to FastAPI.

```
Browser                 Next.js Server              FastAPI           Zitadel
  |                          |                        |                 |
  |-- GET /login ----------->|                        |                 |
  |                          |-- OIDC redirect ------>|                 |-->
  |<-- 302 to Zitadel -------|                        |                 |
  |-- User logs in at Zitadel ---------------------------------------->|
  |<-- Callback with code ---|                        |                 |
  |                          |-- Exchange code (PKCE) ----------------->|
  |                          |<-- access_token + id_token --------------|
  |                          |-- Store token in session cookie          |
  |<-- 302 to /dashboard ----|                        |                 |
  |                          |                        |                 |
  |-- GET /dashboard ------->|                        |                 |
  |                          |-- GET /api/projects -->|                 |
  |                          |   (Bearer: token)      |                 |
  |                          |                        |-- Verify JWT    |
  |                          |                        |   via JWKS ---->|
  |                          |<-- JSON projects ------|                 |
  |<-- Rendered HTML --------|                        |                 |
```

**Why this pattern:**
- Access tokens never reach the browser (stored server-side in encrypted cookie)
- FastAPI's existing JWT validation works unchanged -- it already validates Zitadel tokens with RS256 and JWKS
- No CORS complexity since Next.js server makes the API calls, not the browser
- Server Components can fetch data before rendering (faster initial page loads)

### Auth.js Configuration

```typescript
// auth.ts
import NextAuth from "next-auth"
import Zitadel from "next-auth/providers/zitadel"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Zitadel({
      issuer: `https://${process.env.ZITADEL_DOMAIN}`,
      clientId: process.env.ZITADEL_CLIENT_ID!,
      clientSecret: process.env.ZITADEL_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: "openid email profile urn:zitadel:iam:org:project:roles",
        },
      },
    }),
  ],
  callbacks: {
    jwt({ token, account }) {
      // Capture Zitadel access token during login
      if (account) {
        token.accessToken = account.access_token
        token.expiresAt = account.expires_at
      }
      return token
    },
    session({ session, token }) {
      // Make access token available to server-side code
      session.accessToken = token.accessToken as string
      return session
    },
  },
})
```

### API Client Pattern (Server-Side)

```typescript
// lib/api-client.ts
import { auth } from "@/auth"

const API_BASE = process.env.API_INTERNAL_URL || "http://api:8000"

export async function apiGet<T>(path: string): Promise<T> {
  const session = await auth()
  if (!session?.accessToken) throw new Error("Not authenticated")

  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${session.accessToken}` },
    cache: "no-store",
  })

  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}
```

**Key detail:** Inside Docker Compose, Next.js calls FastAPI at `http://api:8000` (internal Docker network). No external roundtrip. The Nginx proxy is only for external browser requests.

## Recommended Project Structure

```
server/
  webui/                         # New Next.js app
    Dockerfile
    next.config.ts
    auth.ts                      # Auth.js config (Zitadel OIDC)
    middleware.ts                 # Route protection (redirect to login)
    src/
      app/
        layout.tsx               # Root layout with session provider
        page.tsx                 # Landing / redirect to dashboard
        login/
          page.tsx               # Login page
        (authenticated)/         # Route group requiring auth
          layout.tsx             # Auth check layout
          dashboard/
            page.tsx             # Main dashboard
          projects/
            page.tsx             # Project list
            [id]/
              page.tsx           # Project detail
              fiber-plan/
                page.tsx         # Splice closures, trays, splices
              work-orders/
                page.tsx         # Work orders for project
          work-orders/
            page.tsx             # All work orders
            [id]/
              page.tsx           # Work order detail + items + SMR
          sync/
            page.tsx             # Sync status / GPKG management
        api/
          auth/
            [...nextauth]/
              route.ts           # Auth.js API route handler
      lib/
        api-client.ts            # Server-side fetch wrapper with Bearer
        types.ts                 # TypeScript types matching FastAPI models
      components/
        ui/                      # Reusable UI components
        projects/                # Project-specific components
        work-orders/             # Work order components
        fiber-plan/              # Fiber plan components
  api/                           # Existing FastAPI (unchanged)
  db/                            # Existing DB init (unchanged)
  nginx/                         # Updated Nginx configs
  docker-compose.yml             # Updated with webui service
```

### Structure Rationale

- **`(authenticated)/` route group:** Uses Next.js route groups to apply auth layout without affecting URL structure. The layout checks the session and redirects to `/login` if unauthenticated.
- **`lib/api-client.ts`:** Single point for all FastAPI calls. Attaches Bearer token automatically. Easy to add error handling, retries, or caching later.
- **`lib/types.ts`:** TypeScript interfaces matching FastAPI's Pydantic models. Keeps frontend type-safe. These mirror what FastAPI already defines (ProjectOut, WorkOrderOut, etc.).
- **Feature folders under `(authenticated)/`:** Each major API domain (projects, work-orders, fiber-plan, sync) gets its own route subtree, matching the FastAPI router structure.

## Data Flow

### Authentication Flow

```
[Browser] --GET /--> [Next.js middleware]
  |                       |
  |  (no session?)        |-- redirect to /login
  |  (has session?)       |-- continue to page
  |                       |
  |  /login: "Sign in with Zitadel" button
  |       |
  |       v
  |  Auth.js signIn("zitadel")
  |       |
  |       v
  |  Zitadel login page (external)
  |       |
  |       v
  |  Callback: /api/auth/callback/zitadel
  |       |
  |  Auth.js exchanges code for tokens (PKCE)
  |  Stores access_token in encrypted JWT cookie
  |       |
  |       v
  |  Redirect to /dashboard
```

### Data Read Flow (Server Component)

```
[Browser] --GET /projects--> [Next.js Server]
                                  |
                            auth() -- reads session cookie
                                  |
                            apiGet("/projects")
                                  |
                            fetch("http://api:8000/projects",
                                  { Authorization: "Bearer <token>" })
                                  |
                            [FastAPI] validates JWT, returns JSON
                                  |
                            [Next.js] renders React Server Component
                                  |
                            [Browser] receives HTML
```

### Data Write Flow (Server Action)

```
[Browser] --form submit--> [Next.js Server Action]
                                  |
                            auth() -- reads session cookie
                                  |
                            apiPost("/projects", body)
                                  |
                            fetch("http://api:8000/projects",
                                  { method: "POST",
                                    Authorization: "Bearer <token>",
                                    body: JSON.stringify(data) })
                                  |
                            [FastAPI] validates JWT + body, inserts row
                                  |
                            [Next.js] revalidates path, returns result
                                  |
                            [Browser] sees updated UI
```

### Key Data Flows

1. **OIDC Login:** Browser -> Next.js -> Zitadel -> Next.js (stores token in cookie)
2. **API Read:** Next.js Server Component -> FastAPI (Bearer token) -> PostgreSQL -> JSON -> Rendered HTML
3. **API Write:** Browser form -> Next.js Server Action -> FastAPI (Bearer token) -> PostgreSQL -> Revalidate cache
4. **Photo display:** Browser -> Nginx `/storage/photos/` -> static file (direct, no auth needed per current setup)
5. **GPKG sync:** Stays on QGIS/QField clients -> FastAPI `/sync/` endpoints (WebUI shows status only)

## Architectural Patterns

### Pattern 1: Server Components for Data Fetching

**What:** Use React Server Components to fetch data from FastAPI at render time. No client-side loading spinners for initial page loads.
**When to use:** Any page that displays data from the API (project lists, work order details, fiber plan views).
**Trade-offs:** Faster initial load, no loading states; but requires page navigation for updates (or streaming with Suspense boundaries).

```typescript
// app/(authenticated)/projects/page.tsx
import { apiGet } from "@/lib/api-client"
import type { ProjectOut } from "@/lib/types"

export default async function ProjectsPage() {
  const projects = await apiGet<ProjectOut[]>("/projects")

  return (
    <div>
      <h1>Projects</h1>
      {projects.map((p) => (
        <ProjectCard key={p.id} project={p} />
      ))}
    </div>
  )
}
```

### Pattern 2: Server Actions for Mutations

**What:** Use Next.js Server Actions (form actions) to call FastAPI write endpoints. The action runs on the server, attaches the Bearer token, and revalidates the page data.
**When to use:** Create/update/delete operations (create project, change work order status, create splice).
**Trade-offs:** Progressive enhancement (works without JS); but not suited for real-time updates.

```typescript
// app/(authenticated)/projects/actions.ts
"use server"

import { auth } from "@/auth"
import { revalidatePath } from "next/cache"

export async function createProject(formData: FormData) {
  const session = await auth()
  if (!session?.accessToken) throw new Error("Not authenticated")

  const res = await fetch("http://api:8000/projects", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: formData.get("name"),
      description: formData.get("description"),
    }),
  })

  if (!res.ok) throw new Error("Failed to create project")
  revalidatePath("/projects")
}
```

### Pattern 3: Client Components for Interactive UI

**What:** Use client components (`"use client"`) for interactive elements that need state (form inputs, modals, splice tray drag-and-drop). These call Server Actions or use SWR/React Query for polling.
**When to use:** Fiber plan editor, work order status transitions, real-time sync status.
**Trade-offs:** Full interactivity; but tokens are not directly accessible (must go through server route or action).

### Pattern 4: Middleware for Route Protection

**What:** Next.js middleware intercepts all requests and checks for a valid session before allowing access to protected routes.
**When to use:** Always -- applied globally with exceptions for `/login`, `/api/auth`, and static assets.

```typescript
// middleware.ts
export { auth as middleware } from "@/auth"

export const config = {
  matcher: ["/((?!login|api/auth|_next/static|_next/image|favicon.ico).*)"],
}
```

## Docker Compose Integration

### Updated docker-compose.yml (additions)

```yaml
services:
  webui:
    build:
      context: ./webui
      dockerfile: Dockerfile
    container_name: fiberq-webui
    environment:
      ZITADEL_DOMAIN: ${ZITADEL_DOMAIN}
      ZITADEL_CLIENT_ID: ${WEBUI_ZITADEL_CLIENT_ID}
      ZITADEL_CLIENT_SECRET: ${WEBUI_ZITADEL_CLIENT_SECRET}
      NEXTAUTH_URL: ${WEBUI_PUBLIC_URL:-https://fiberq.example.com}
      NEXTAUTH_SECRET: ${WEBUI_SESSION_SECRET}
      API_INTERNAL_URL: http://api:8000
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped

  nginx:
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - photos:/app/storage/photos:ro
    depends_on:
      api:
        condition: service_healthy
      webui:
        condition: service_started
```

### Updated Nginx Configuration

```nginx
upstream api {
    server api:8000;
}

upstream webui {
    server webui:3000;
}

server {
    listen 80;
    server_name _;

    # API proxy -- existing, unchanged
    location /api/ {
        proxy_pass http://api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }

    # Health check -- existing, unchanged
    location /health {
        proxy_pass http://api/health;
    }

    # Static photos -- existing, unchanged
    location /storage/photos/ {
        alias /app/storage/photos/;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # WebUI -- everything else goes to Next.js
    location / {
        proxy_pass http://webui;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Key change:** The `location /` block switches from serving static HTML files to proxying to the Next.js container. The `/api/` and `/storage/` blocks remain unchanged.

### Next.js Dockerfile (Standalone)

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
```

Requires `output: "standalone"` in `next.config.ts`. Produces a ~150-200MB image.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Next.js Directly Querying PostgreSQL

**What people do:** Install `pg` or `drizzle-orm` in Next.js and query the database directly from Server Components.
**Why it's wrong:** Duplicates all authorization logic that FastAPI already implements. The role checks in `auth/roles.py` (require_admin, require_engineer, require_field_worker) would need to be reimplemented. Two services touching the same tables creates schema coupling and migration nightmares.
**Do this instead:** Always go through FastAPI. The extra HTTP hop within Docker's internal network adds <1ms latency.

### Anti-Pattern 2: Exposing Access Tokens to the Browser

**What people do:** Store the Zitadel access token in localStorage or a client-readable cookie, then make API calls directly from browser JavaScript.
**Why it's wrong:** XSS attacks can steal the token. The token has full API access. CORS configuration becomes complex.
**Do this instead:** Keep tokens server-side in Auth.js encrypted cookies. Client components call Next.js Server Actions or API route handlers, which attach the token server-side.

### Anti-Pattern 3: Building a "Mini Backend" in Next.js Route Handlers

**What people do:** Create Next.js API routes that do data transformation, business logic, or complex queries before/after calling FastAPI.
**Why it's wrong:** Business logic belongs in FastAPI. Having logic in two places makes debugging harder and creates inconsistency between WebUI and QGIS/QField clients.
**Do this instead:** Next.js route handlers should be thin pass-through layers: authenticate, forward to FastAPI, return result. If new business logic is needed, add it to FastAPI.

### Anti-Pattern 4: Using Client-Side Fetch to FastAPI Directly

**What people do:** Configure CORS on FastAPI and have browser JavaScript call `/api/projects` directly with a token.
**Why it's wrong:** Requires CORS configuration, token management in the browser, and loses Server Component benefits. Also means the QGIS mobile clients and browser clients have different auth flows.
**Do this instead:** All browser-initiated data requests go through Next.js (Server Components for reads, Server Actions for writes). Next.js handles the token forwarding internally.

## Scaling Considerations

| Concern | Current scale (1-10 users) | At 50 users | At 500+ users |
|---------|---------------------------|-------------|---------------|
| **Next.js instances** | 1 container, single process | 1 container is fine | Multiple workers or replicas behind Nginx |
| **FastAPI workers** | 4 uvicorn workers (current) | 4 workers is fine | 8-16 workers, or multiple containers |
| **PostgreSQL** | Single instance | Single instance | Read replicas if needed |
| **Session storage** | Auth.js JWT cookies (stateless) | No scaling concern | No scaling concern |
| **Static assets** | Nginx serves photos | Nginx serves photos | CDN for photos via Cloudflare |

### Scaling Priorities

1. **First bottleneck:** FastAPI worker count if many concurrent GPKG sync operations (CPU-intensive geodata processing). Fix: increase `--workers` count.
2. **Second bottleneck:** PostgreSQL connection pool if many concurrent requests. Fix: increase asyncpg pool `max_size` (currently 20).
3. **Next.js is unlikely to bottleneck** for this user scale -- it is primarily rendering HTML and forwarding API calls.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Zitadel** | OIDC Authorization Code + PKCE via Auth.js | Next.js handles login/logout. FastAPI validates tokens via JWKS. Separate client IDs for WebUI vs API. |
| **Cloudflare Tunnel** | Connects to Nginx, provides public HTTPS | No code changes needed. Tunnel config just points at nginx:80. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Browser <-> Nginx | HTTPS (via Cloudflare Tunnel) | TLS terminated at Cloudflare |
| Nginx <-> Next.js | HTTP on Docker network | `proxy_pass http://webui:3000` |
| Nginx <-> FastAPI | HTTP on Docker network | `proxy_pass http://api:8000` (path `/api/` stripped) |
| Next.js <-> FastAPI | HTTP on Docker network | `fetch("http://api:8000/...")` with Bearer token |
| FastAPI <-> PostgreSQL | TCP on Docker network | asyncpg pool, port 5432 |
| Next.js <-> Zitadel | HTTPS (external) | OIDC flow during login only |
| FastAPI <-> Zitadel | HTTPS (external) | JWKS fetch for JWT verification (cached) |

### Zitadel Configuration Requirements

Two application registrations in Zitadel:

1. **Existing API application** (Resource Server): Used by FastAPI for JWT validation. Already configured.
2. **New WebUI application** (Web/PKCE): Registered as a web application with Authorization Code + PKCE flow.
   - Redirect URI: `https://{DOMAIN}/api/auth/callback/zitadel`
   - Post-logout redirect URI: `https://{DOMAIN}`
   - Grant type: Authorization Code
   - Auth method: PKCE (but Auth.js also needs a client secret configured)
   - Must request scope: `openid email profile urn:zitadel:iam:org:project:roles`

The WebUI's Zitadel client ID will differ from the API's client ID. FastAPI validates tokens using the API's client ID as the `audience`. For this to work, both applications must be in the same Zitadel project, and the token's audience must include the API's client ID.

**Important:** Configure "Project Role Assertion" in Zitadel to include `urn:zitadel:iam:org:project:roles` in tokens. This is what FastAPI's `_extract_roles()` reads.

## Build Order (Dependencies Between Components)

```
Phase 1: Next.js scaffold + Auth.js + Zitadel login
    (depends on: Zitadel WebUI app registration)
    (does not depend on: any FastAPI changes)

Phase 2: API client library + type definitions
    (depends on: Phase 1 for session/token access)
    (depends on: FastAPI API being stable -- it already is)

Phase 3: Core pages (dashboard, projects, work orders)
    (depends on: Phases 1+2 for auth + API client)

Phase 4: Docker integration (Dockerfile, compose, Nginx update)
    (depends on: Phase 1 at minimum for a working build)
    (can be done in parallel with Phase 3)

Phase 5: Advanced pages (fiber plan editor, sync status)
    (depends on: Phase 3 for navigation/layout patterns)
    (highest UI complexity -- splice tray visualization)
```

No changes to FastAPI are required for the WebUI to work. The existing API, auth validation, and CORS configuration (`allow_origins=["*"]`) already support the integration pattern described here.

## Sources

- [Zitadel Next.js SDK examples](https://zitadel.com/docs/sdk-examples/nextjs) -- Official Zitadel docs for Next.js integration (HIGH confidence)
- [Auth.js Zitadel provider](https://authjs.dev/getting-started/providers/zitadel) -- Auth.js official provider docs (HIGH confidence)
- [Auth.js: Integrating Third Party Backends](https://authjs.dev/guides/integrating-third-party-backends) -- Token forwarding pattern (HIGH confidence)
- [Next.js Backend for Frontend guide](https://nextjs.org/docs/app/guides/backend-for-frontend) -- Official Next.js BFF pattern documentation, version 16.1.6 (HIGH confidence)
- [Zitadel example-auth-nextjs](https://github.com/zitadel/example-auth-nextjs) -- Reference implementation with PKCE flow (HIGH confidence)
- Existing codebase: `server/api/auth/zitadel.py` -- Current JWT validation logic (verified, PRIMARY SOURCE)
- Existing codebase: `server/nginx/nginx.conf` -- Current routing config with WebUI placeholder (verified, PRIMARY SOURCE)
- Existing codebase: `server/docker-compose.yml` -- Current service topology (verified, PRIMARY SOURCE)

---
*Architecture research for: FiberQ WebUI (Next.js frontend for FTTX management)*
*Researched: 2026-02-21*

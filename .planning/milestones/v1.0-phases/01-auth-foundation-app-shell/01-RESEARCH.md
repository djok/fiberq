# Phase 1: Auth Foundation & App Shell - Research

**Researched:** 2026-02-21
**Domain:** Next.js 16 + Zitadel OIDC + Auth.js v5 + shadcn/ui + next-intl
**Confidence:** HIGH

## Summary

This phase delivers a Next.js 16 application integrated with Zitadel via Auth.js v5 (next-auth@beta), wrapped in a responsive sidebar shell with bilingual support (Bulgarian + English). The technical landscape is well-documented but has several critical integration points that require careful ordering: (1) Auth.js v5 must forward the raw Zitadel access_token to the existing FastAPI backend (not the NextAuth JWE), (2) the `proxy.ts` file (Next.js 16's replacement for `middleware.ts`) must compose both auth protection and i18n locale routing, (3) the existing FastAPI CORS configuration (`allow_origins=["*"]` with `allow_credentials=True`) is spec-invalid and must be fixed, and (4) Zitadel requires three independent settings enabled to include role claims in tokens.

Next.js 16.1.6 is the current stable release (October 2025), using Turbopack as default bundler, `proxy.ts` instead of `middleware.ts`, and React 19.2. Auth.js v5 remains at `next-auth@5.0.0-beta.30` -- it has not reached stable, and Auth.js is now in maintenance mode under Better Auth stewardship. However, it has a built-in Zitadel provider, an official Zitadel example repository, and is production-proven. For this project, Auth.js v5 remains the correct choice given the existing Zitadel ecosystem integration.

**Primary recommendation:** Use Next.js 16.1.x with Auth.js v5 (`next-auth@beta`), shadcn/ui sidebar, next-intl 4.x, and next-themes for dark mode. Deploy as standalone Docker image behind the existing Nginx reverse proxy. Fix CORS on FastAPI immediately.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Direct redirect to Zitadel login -- no intermediate FiberQ landing page
- Auth errors (wrong password, deactivated account) handled entirely by Zitadel's login UI
- After successful login: role-based redirect -- Admin goes to User Management (placeholder), others go to Projects (placeholder)
- Session expiry: silent token refresh without user interruption (refresh token via `offline_access` scope)
- Collapsible sidebar navigation -- full labels on desktop, collapses to icons on tablet/narrow viewport
- Admin sees: Dashboard, Projects, Users, Profile, Logout (full set)
- Non-admin roles see subset: items hidden based on role (e.g., Field Worker sees no Users link)
- FiberQ logo + name displayed in sidebar header
- Profile page shows: name, email, role, assigned projects list, last login timestamp
- Avatar: use Zitadel avatar if available (from userinfo endpoint), fallback to generated initials avatar
- All profile data is read-only with "Edit profile" link opening Zitadel account page in new tab
- Assigned projects list is a placeholder in Phase 1
- Color scheme: green/teal -- telecom/infrastructure feel
- Theme: follows system preference (prefers-color-scheme), automatic light/dark switching
- Interface style: data-dense, compact -- more information per screen (like Jira, Grafana)
- Language: bilingual (Bulgarian + English) with language switcher from day one

### Claude's Discretion
- Exact green/teal color palette values (primary, secondary, accent)
- Mobile navigation pattern (hamburger menu vs collapsible sidebar)
- Loading skeleton design and error state layouts
- Typography choices within "data-dense" constraint
- Exact spacing, padding, border-radius values
- i18n implementation approach (next-intl, custom, etc.)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | App Router framework | Current stable; Turbopack default, proxy.ts, React 19.2 |
| next-auth | 5.0.0-beta.30 | Auth.js v5 with Zitadel provider | Built-in Zitadel provider, PKCE flow, official example repo |
| TypeScript | 5.9.3 | Type safety | Required by Next.js 16 (min 5.1.0) |
| Tailwind CSS | 4.2.0 | Utility-first CSS | CSS-first config (no tailwind.config.js), 100x faster incremental builds |
| shadcn/ui | latest | Component system | Tailwind v4 + React 19 compatible, sidebar component built-in |
| next-intl | 4.8.3 | i18n (Bulgarian + English) | Server Component native, App Router first-class, ~2KB bundle |
| next-themes | latest | Dark/light mode | System preference support, shadcn/ui recommended integration |
| React | 19.2.x | UI library | Bundled with Next.js 16, includes View Transitions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tailwindcss/postcss | latest | PostCSS plugin for Tailwind v4 | Required for Tailwind v4 CSS-first setup |
| postcss | latest | CSS processing | Required by Tailwind v4 |
| lucide-react | latest | Icon library | shadcn/ui default icon set, used in sidebar navigation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Auth.js v5 (next-auth@beta) | Better Auth | Better Auth is the future direction, but lacks built-in Zitadel provider; would need generic OIDC plugin. Auth.js v5 has official Zitadel example and is still receiving security patches. |
| next-intl | next-i18next | next-i18next is Pages Router focused; next-intl is App Router native with Server Component support |
| next-themes | Manual prefers-color-scheme | next-themes handles hydration, SSR flash prevention, and system preference detection |

**Installation:**
```bash
# Create Next.js 16 project
npx create-next-app@latest web --typescript --app --tailwind --turbopack

# Auth
npm install next-auth@beta

# i18n
npm install next-intl

# Theme
npm install next-themes

# shadcn/ui initialization (interactive)
npx shadcn@latest init

# shadcn/ui components needed for this phase
npx shadcn@latest add sidebar button avatar dropdown-menu skeleton separator sheet tooltip
```

## Architecture Patterns

### Recommended Project Structure
```
web/                              # Next.js app root (sibling to server/)
├── src/
│   ├── app/
│   │   ├── [locale]/             # next-intl locale segment
│   │   │   ├── layout.tsx        # Authenticated shell layout (sidebar + content)
│   │   │   ├── page.tsx          # Root redirect (based on role)
│   │   │   ├── profile/
│   │   │   │   └── page.tsx      # Profile page
│   │   │   ├── projects/
│   │   │   │   └── page.tsx      # Placeholder
│   │   │   ├── users/
│   │   │   │   └── page.tsx      # Placeholder (admin only)
│   │   │   └── dashboard/
│   │   │       └── page.tsx      # Placeholder
│   │   ├── api/
│   │   │   └── auth/
│   │   │       └── [...nextauth]/
│   │   │           └── route.ts  # Auth.js route handler
│   │   └── layout.tsx            # Root layout (html, body, providers)
│   ├── auth.ts                   # Auth.js configuration (Zitadel provider, callbacks)
│   ├── auth.config.ts            # Auth config without adapter (for proxy.ts edge compat)
│   ├── proxy.ts                  # Next.js 16 proxy (auth + i18n composition)
│   ├── i18n/
│   │   ├── routing.ts            # next-intl locale config (en, bg)
│   │   ├── navigation.ts         # Locale-aware Link, redirect, useRouter
│   │   └── request.ts            # Server-side locale resolution
│   ├── components/
│   │   ├── ui/                   # shadcn/ui generated components
│   │   ├── app-sidebar.tsx       # Main sidebar with role-based nav
│   │   ├── sidebar-nav.tsx       # Navigation items with role filtering
│   │   ├── user-nav.tsx          # User avatar + dropdown (profile, logout)
│   │   ├── theme-toggle.tsx      # Light/dark/system toggle
│   │   ├── language-switcher.tsx  # BG/EN language toggle
│   │   └── providers.tsx         # Combined providers (session, theme, intl)
│   ├── lib/
│   │   ├── utils.ts              # shadcn/ui cn() utility
│   │   ├── roles.ts              # Role constants, permission helpers
│   │   └── api.ts                # API client (forwards access_token to FastAPI)
│   ├── messages/
│   │   ├── en.json               # English translations
│   │   └── bg.json               # Bulgarian translations
│   └── types/
│       └── next-auth.d.ts        # Auth.js type augmentation (accessToken, roles)
├── public/
│   └── logo.svg                  # FiberQ logo
├── next.config.ts                # standalone output, next-intl plugin
├── postcss.config.mjs            # @tailwindcss/postcss
├── Dockerfile                    # Multi-stage standalone build
└── .env.local                    # Local dev environment variables
```

### Pattern 1: Auth.js v5 Configuration with Zitadel + Token Forwarding

**What:** Configure Auth.js with Zitadel OIDC provider, forwarding the raw access_token (not the NextAuth JWE) to the existing FastAPI backend.
**When to use:** Every authenticated API call from Next.js to FastAPI.
**Critical pitfall addressed:** Pitfall #3 (NextAuth JWE forwarded to FastAPI instead of Zitadel JWT)

```typescript
// src/auth.ts
import NextAuth from "next-auth";
import Zitadel from "next-auth/providers/zitadel";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Zitadel({
      issuer: process.env.ZITADEL_ISSUER,         // https://your-instance.zitadel.cloud
      clientId: process.env.AUTH_ZITADEL_ID!,
      clientSecret: process.env.AUTH_ZITADEL_SECRET!,
      authorization: {
        params: {
          scope: [
            "openid",
            "profile",
            "email",
            "offline_access",                       // For refresh tokens
            "urn:zitadel:iam:org:projects:roles",   // For role claims
          ].join(" "),
        },
      },
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account }) {
      // On initial sign-in, capture the raw Zitadel tokens
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.idToken = account.id_token;
        token.expiresAt = account.expires_at;

        // Extract roles from the Zitadel access_token claims
        // Roles are in urn:zitadel:iam:org:project:roles or
        // urn:zitadel:iam:org:project:{projectId}:roles
      }

      // Silent token refresh when access_token expires
      if (token.expiresAt && Date.now() / 1000 > (token.expiresAt as number)) {
        // Refresh token logic here
      }

      return token;
    },
    async session({ session, token }) {
      // Forward the RAW Zitadel access_token to the session
      // This is what gets sent to FastAPI -- NOT the NextAuth JWE
      session.accessToken = token.accessToken as string;
      session.user.roles = token.roles as string[];
      return session;
    },
  },
});
```

### Pattern 2: Proxy Composition (Auth + i18n)

**What:** Compose Auth.js auth checks with next-intl locale routing in a single `proxy.ts`.
**When to use:** Every request to the application.
**Critical pitfall addressed:** Pitfall #6 (NextAuth route conflict with Nginx /api/ prefix)

```typescript
// src/proxy.ts
import { auth } from "./auth";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const intlMiddleware = createIntlMiddleware(routing);

// Public paths that don't require auth
const publicPaths = ["/api/auth"];

export default async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip auth for NextAuth API routes
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Check authentication
  const session = await auth();
  if (!session) {
    // Redirect to Zitadel login (via NextAuth signIn)
    return NextResponse.redirect(new URL("/api/auth/signin/zitadel", request.url));
  }

  // Apply i18n routing for authenticated requests
  return intlMiddleware(request);
}

export const config = {
  matcher: "/((?!_next|_vercel|.*\\..*).*)",
};
```

### Pattern 3: Role-Based Navigation Filtering

**What:** Filter sidebar navigation items based on user roles from the Zitadel token.
**When to use:** Sidebar rendering.

```typescript
// src/lib/roles.ts
export const ROLES = {
  ADMIN: "admin",
  ENGINEER: "engineer",
  FIELD_WORKER: "field_worker",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

interface NavItem {
  title: string;        // i18n key
  href: string;
  icon: string;
  requiredRoles?: Role[];  // Empty = visible to all authenticated users
}

export const NAV_ITEMS: NavItem[] = [
  { title: "nav.dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { title: "nav.projects", href: "/projects", icon: "FolderKanban" },
  { title: "nav.users", href: "/users", icon: "Users", requiredRoles: ["admin"] },
  { title: "nav.profile", href: "/profile", icon: "UserCircle" },
];

export function filterNavByRole(items: NavItem[], userRoles: string[]): NavItem[] {
  return items.filter((item) => {
    if (!item.requiredRoles || item.requiredRoles.length === 0) return true;
    return item.requiredRoles.some((role) => userRoles.includes(role));
  });
}
```

### Pattern 4: Forwarding access_token to FastAPI

**What:** Server-side API calls from Next.js to FastAPI using the raw Zitadel JWT.
**When to use:** Any data fetching from Next.js server components/actions to FastAPI.
**Critical pitfall addressed:** Pitfall #1 (JWT audience mismatch) and #3 (JWE instead of JWT)

```typescript
// src/lib/api.ts
import { auth } from "@/auth";

const API_BASE = process.env.INTERNAL_API_URL || "http://api:8000";

export async function apiFetch(path: string, options?: RequestInit) {
  const session = await auth();
  if (!session?.accessToken) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${session.accessToken}`,  // Raw Zitadel JWT
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}
```

### Pattern 5: Zitadel Federated Logout

**What:** End both the local NextAuth session AND the Zitadel server session.
**When to use:** Logout action from any page.

```typescript
// Logout must redirect to Zitadel's end_session_endpoint
// URL format: https://{ZITADEL_DOMAIN}/oidc/v1/end_session
//   ?id_token_hint={id_token}
//   &post_logout_redirect_uri={app_url}
//   &state={random_string}
//
// Auth.js signOut() only clears the local session.
// For full federated logout, redirect to Zitadel after clearing local session.
```

### Anti-Patterns to Avoid
- **Forwarding NextAuth JWE to FastAPI:** The `session.accessToken` must be the raw Zitadel-issued JWT, not the encrypted NextAuth session token. FastAPI validates against Zitadel's JWKS endpoint.
- **Using `middleware.ts` instead of `proxy.ts`:** Next.js 16 deprecated `middleware.ts` in favor of `proxy.ts`. The old name still works but is deprecated and will be removed.
- **Validating tokens in proxy.ts:** Proxy should only do optimistic checks (is session cookie present?). Full token validation happens in the backend.
- **Using `allow_origins=["*"]` with `allow_credentials=True`:** This is spec-invalid per the Fetch spec. Must use explicit origin.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OIDC authentication flow | Custom PKCE implementation | Auth.js v5 Zitadel provider | PKCE, token refresh, session management all built-in |
| Sidebar navigation | Custom collapsible sidebar | shadcn/ui `Sidebar` component | Built-in collapsible=icon mode, mobile sheet, keyboard shortcut, RTL |
| Dark mode | Manual CSS class toggling | next-themes + shadcn/ui | Handles SSR hydration flash, system preference, localStorage |
| i18n routing | Custom locale detection | next-intl middleware | Accept-Language negotiation, cookie persistence, SEO alternate links |
| JWT token refresh | Custom refresh timer | Auth.js jwt callback | Automatic refresh on session access, handles race conditions |
| Avatar initials | Custom canvas drawing | CSS-based initials in shadcn Avatar fallback | Simple, accessible, no canvas overhead |
| Responsive sidebar | Media queries + state | shadcn/ui SidebarProvider | Built-in responsive breakpoints, CSS variables, Sheet on mobile |

**Key insight:** The shadcn/ui Sidebar component already implements collapsible-to-icons behavior (`collapsible="icon"`) and mobile Sheet behavior. Do not build a custom sidebar.

## Common Pitfalls

### Pitfall 1: JWT Audience Mismatch Between Frontend and Backend
**What goes wrong:** FastAPI validates `audience` against its own `ZITADEL_CLIENT_ID`. If the Next.js app uses a different Zitadel application (different client_id), the `aud` claim won't match and all API calls fail with 401.
**Why it happens:** Zitadel allows multiple applications per project. The frontend (Web app) and backend (API app) may have different client IDs but share the same project.
**How to avoid:** Configure the FastAPI backend to validate audience against the Zitadel **project ID** (using `urn:zitadel:iam:org:project:id:{projectId}:aud` scope), or ensure both apps use the same client_id. The existing backend code (`server/api/auth/zitadel.py` line 89) validates `audience=settings.zitadel_client_id` -- this must be reviewed.
**Warning signs:** 401 errors on every API call despite valid login.

### Pitfall 2: CORS Wildcard with Credentials
**What goes wrong:** The existing FastAPI app (`server/api/main.py` lines 41-47) has `allow_origins=["*"]` with `allow_credentials=True`. Per the Fetch spec, browsers reject this combination.
**Why it happens:** Common during development when "just make it work" leads to `*` origins.
**How to avoid:** Change `allow_origins` to the specific Next.js origin (e.g., `["http://localhost:3000"]` in dev, the actual domain in production). Since Next.js and FastAPI will share the same Nginx/Cloudflare domain, CORS may not even be needed for production (same-origin requests). But the fix is still required for local development where ports differ.
**Warning signs:** Browser console shows CORS errors on every fetch with credentials.

### Pitfall 3: NextAuth JWE Forwarded to FastAPI Instead of Zitadel JWT
**What goes wrong:** Auth.js encrypts its session token as a JWE. If you accidentally send this JWE to FastAPI instead of the raw Zitadel access_token, FastAPI's `python-jose` library cannot decode it (wrong key, wrong format).
**How to avoid:** In the `jwt` callback, store `account.access_token` (the raw Zitadel JWT) in the token object. In the `session` callback, expose it as `session.accessToken`. When calling FastAPI, use `session.accessToken`, never the NextAuth session cookie value.
**Warning signs:** FastAPI returns "Invalid token header" or "Token signing key not found".

### Pitfall 4: Zitadel Role Claims Missing from Token
**What goes wrong:** Roles don't appear in the JWT even though they're assigned in Zitadel.
**Why it happens:** Three independent settings must ALL be enabled:
  1. **Project > General > "Assert Roles on Authentication"** -- returns roles from userinfo endpoint
  2. **Application > Token Settings > "User Roles Inside ID Token"** -- includes roles in ID token
  3. **OIDC scope must include `urn:zitadel:iam:org:projects:roles`** -- requests role claims
**How to avoid:** Verify all three settings. The roles appear as:
```json
{
  "urn:zitadel:iam:org:project:roles": {
    "admin": { "org_id": "org_domain" },
    "engineer": { "org_id": "org_domain" }
  }
}
```
The existing backend code (`server/api/auth/zitadel.py` lines 102-120) already handles both `urn:zitadel:iam:org:project:roles` and `urn:zitadel:iam:org:project:{id}:roles` claim formats -- the frontend must use the same extraction logic.
**Warning signs:** `_extract_roles()` returns empty array despite user having roles in Zitadel console.

### Pitfall 5: NextAuth Route Conflict with Nginx /api/ Prefix
**What goes wrong:** The existing Nginx config (`server/nginx/nginx.conf` lines 22-37) forwards `/api/*` to FastAPI. NextAuth's default route is `/api/auth/[...nextauth]`. If Nginx forwards `/api/auth/*` to FastAPI, the auth callback never reaches Next.js.
**Why it happens:** Nginx location matching intercepts `/api/auth/callback/zitadel` and sends it to FastAPI.
**How to avoid:** Update Nginx to route `/api/auth/*` to the Next.js container, not FastAPI. Or use a different path prefix for the FastAPI backend. The current Nginx config strips `/api/` when proxying to FastAPI (`proxy_pass http://api/;` -- note trailing slash), so requests to `/api/auth/callback/zitadel` become `/auth/callback/zitadel` on FastAPI, which is a 404. This needs explicit routing.
**Warning signs:** OAuth callback returns 404 or hits the wrong backend.

### Pitfall 6: CVE-2025-29927 -- Next.js Middleware Bypass
**What goes wrong:** Attacker spoofs the `x-middleware-subrequest` header to bypass proxy/middleware auth checks.
**Why it happens:** Vulnerability in Next.js before 14.2.25 and 15.2.3. Fixed in Next.js 16.x.
**How to avoid:** Use Next.js >= 15.2.3 (we're using 16.1.6, which includes the fix). Additionally, the Nginx reverse proxy should strip the `x-middleware-subrequest` header from external requests as defense-in-depth.
**Warning signs:** Unauthenticated access to protected routes.

### Pitfall 7: next-intl + Auth.js Proxy Composition Order
**What goes wrong:** If i18n middleware runs before auth check, unauthenticated users get locale-redirected instead of login-redirected, causing redirect loops.
**Why it happens:** Both next-intl and Auth.js want to control redirects in `proxy.ts`.
**How to avoid:** Auth check FIRST, then i18n routing. See Pattern 2 above. Skip i18n for `/api/auth/*` paths entirely.
**Warning signs:** Infinite redirect loops on unauthenticated access.

### Pitfall 8: Standalone Docker Output Missing Static Files
**What goes wrong:** Next.js standalone build doesn't include the `public/` and `.next/static/` directories.
**Why it happens:** Standalone mode traces only Node.js dependencies, not static assets.
**How to avoid:** In the Dockerfile, explicitly copy `public/` and `.next/static/` into the standalone directory:
```dockerfile
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
```
**Warning signs:** 404 errors for CSS, JS, images, or fonts in production.

## Code Examples

### Auth.js Type Augmentation
```typescript
// src/types/next-auth.d.ts
import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session extends DefaultSession {
    accessToken?: string;
    user: {
      roles: string[];
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    idToken?: string;
    expiresAt?: number;
    roles?: string[];
    error?: string;
  }
}
```

### next-intl Routing Configuration
```typescript
// src/i18n/routing.ts
import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en", "bg"],
  defaultLocale: "en",
});
```

```typescript
// src/i18n/navigation.ts
import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
```

```typescript
// src/i18n/request.ts
import { getRequestConfig } from "next-intl/server";
import { hasLocale } from "next-intl";
import { routing } from "./routing";

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
```

### next.config.ts with Standalone Output and next-intl
```typescript
// next.config.ts
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig = {
  output: "standalone" as const,
};

export default withNextIntl(nextConfig);
```

### Theme Provider Setup with System Preference
```typescript
// src/components/providers.tsx
"use client";

import { SessionProvider } from "next-auth/react";
import { ThemeProvider } from "next-themes";
import { NextIntlClientProvider } from "next-intl";

export function Providers({
  children,
  locale,
  messages,
}: {
  children: React.ReactNode;
  locale: string;
  messages: Record<string, unknown>;
}) {
  return (
    <SessionProvider>
      <NextIntlClientProvider locale={locale} messages={messages}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </NextIntlClientProvider>
    </SessionProvider>
  );
}
```

### shadcn/ui Sidebar with Collapsible Icon Mode
```typescript
// src/components/app-sidebar.tsx
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarGroup,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarRail,
} from "@/components/ui/sidebar";

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader>
        {/* FiberQ logo + name -- name hidden when collapsed */}
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            {/* Role-filtered nav items */}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        {/* User avatar + name + logout */}
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
```

### Multi-Stage Dockerfile for Next.js Standalone
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Standalone output does NOT include public/ and .next/static/
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
```

### Nginx Configuration Update (Fix API Route Conflict)
```nginx
# Updated server block -- add BEFORE the /api/ location
location /api/auth/ {
    # Route NextAuth callbacks to the Next.js container
    proxy_pass http://web:3000/api/auth/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Strip x-middleware-subrequest header (CVE-2025-29927 defense-in-depth)
proxy_set_header x-middleware-subrequest "";

location /api/ {
    # Existing FastAPI proxy -- unchanged
    proxy_pass http://api/;
    # ... existing headers ...
}

location / {
    # Route to Next.js instead of static files
    proxy_pass http://web:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Color Palette Recommendation (Claude's Discretion)

For the green/teal telecom/infrastructure feel with data-dense UI:

```css
/* Light mode -- CSS variables for shadcn/ui theming */
--primary: oklch(0.55 0.15 165);         /* Teal-600 -- main actions, active states */
--primary-foreground: oklch(0.98 0.01 165);
--secondary: oklch(0.92 0.04 165);       /* Teal-50 -- subtle backgrounds */
--secondary-foreground: oklch(0.25 0.06 165);
--accent: oklch(0.85 0.06 165);          /* Teal-100 -- hover states */
--accent-foreground: oklch(0.25 0.06 165);
--muted: oklch(0.95 0.02 250);           /* Slate-50 -- muted backgrounds */
--muted-foreground: oklch(0.55 0.02 250);
--destructive: oklch(0.55 0.2 25);       /* Red for errors/danger */
--border: oklch(0.85 0.02 250);
--ring: oklch(0.55 0.15 165);            /* Focus ring matches primary */
--radius: 0.375rem;                      /* 6px -- compact feel */

/* Dark mode */
--primary: oklch(0.65 0.15 165);         /* Brighter teal for dark bg */
--background: oklch(0.15 0.02 250);      /* Very dark slate */
--card: oklch(0.18 0.02 250);
```

**Typography for data-dense UI:**
- Base font size: 14px (0.875rem) instead of default 16px
- Use `font-variant-numeric: tabular-nums` for data columns
- Line height: 1.4 (tighter than default 1.5)
- Compact spacing: reduce default shadcn padding by ~25%

## Mobile Navigation Recommendation (Claude's Discretion)

Use shadcn/ui Sidebar's built-in mobile behavior: on viewports below `768px`, the sidebar renders as a **Sheet** (slide-over panel) triggered by a hamburger button. This is the default behavior of the `SidebarProvider` component and requires no custom implementation.

- Desktop (>= 1024px): Full sidebar with labels
- Tablet (768px - 1023px): Collapsed sidebar (icons only) via `collapsible="icon"`
- Mobile (< 768px): Sheet overlay triggered by `SidebarTrigger`

## i18n Recommendation (Claude's Discretion)

Use **next-intl 4.x** with locale-prefixed routing (`/en/...`, `/bg/...`).

Rationale:
- Native Server Component support (translations rendered server-side, zero client JS)
- Built-in proxy.ts composition support
- Type-safe message keys
- ~2KB client bundle
- Active maintenance, v4.8.3 current

Translation file structure:
```json
// messages/en.json
{
  "nav": {
    "dashboard": "Dashboard",
    "projects": "Projects",
    "users": "User Management",
    "profile": "Profile",
    "logout": "Sign Out"
  },
  "profile": {
    "title": "My Profile",
    "name": "Name",
    "email": "Email",
    "role": "Role",
    "projects": "Assigned Projects",
    "lastLogin": "Last Login",
    "editProfile": "Edit Profile",
    "noProjects": "No projects assigned yet"
  },
  "common": {
    "loading": "Loading...",
    "error": "An error occurred",
    "language": "Language"
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `middleware.ts` | `proxy.ts` | Next.js 16 (Oct 2025) | File rename; edge runtime deprecated for proxy |
| `tailwind.config.js` | CSS-first `@import "tailwindcss"` | Tailwind v4 (Jan 2025) | No JS config file needed; use `@theme` directive |
| `next-auth@4` (latest) | `next-auth@beta` (v5) | Auth.js v5 beta (ongoing) | Universal `auth()`, JWT strategy, `proxy.ts` support |
| Auth.js independent | Auth.js under Better Auth | Sep 2025 | Maintenance mode; security patches continue |
| next-intl v3 | next-intl v4 | 2025 | Streamlined API, type-safe config, GDPR cookie changes |
| `experimental.ppr` | `cacheComponents` | Next.js 16 | PPR flag removed; Cache Components replace it |

**Deprecated/outdated:**
- `middleware.ts`: Renamed to `proxy.ts` in Next.js 16. Still works but deprecated.
- `next lint`: Removed in Next.js 16. Use ESLint directly.
- `tailwind.config.js`: Not needed with Tailwind v4 CSS-first approach.
- Sync `params` / `searchParams`: Must use `await params`, `await searchParams` in Next.js 16.

## Open Questions

1. **JWT Audience Validation Strategy**
   - What we know: FastAPI validates `audience=settings.zitadel_client_id`. The Next.js app will have a different `client_id` than the API app in Zitadel.
   - What's unclear: Whether the existing Zitadel project is configured with the `urn:zitadel:iam:org:project:id:{projectId}:aud` scope, which would include the project ID in the audience claim.
   - Recommendation: During implementation, check the Zitadel project config. If audience mismatch occurs, either (a) add the project audience scope, or (b) change FastAPI to validate `issuer` only and check project roles instead of audience.

2. **Zitadel Client Secret Requirement**
   - What we know: Auth.js Zitadel provider seems to require `clientSecret`. Zitadel Web apps with PKCE typically don't need a client secret (public clients).
   - What's unclear: Whether Auth.js v5 Zitadel provider works without a secret, or if a dummy/empty secret is needed.
   - Recommendation: The official Zitadel example uses `ZITADEL_CLIENT_SECRET` described as "a randomly generated string" -- this suggests Auth.js requires it for internal session encryption, not for the OIDC flow itself. Generate a random string.

3. **Zitadel Userinfo Avatar URL**
   - What we know: Profile page should show Zitadel avatar if available.
   - What's unclear: Whether Zitadel includes an avatar/picture URL in the userinfo endpoint or ID token claims.
   - Recommendation: Check the Zitadel userinfo response. Auth.js exposes `session.user.image` from the OIDC `picture` claim. If Zitadel doesn't provide it, fall back to initials avatar.

4. **Docker Compose Integration**
   - What we know: The existing `docker-compose.yml` has api, nginx, postgis, cloudflared services.
   - What's unclear: Whether the web service should be added to the same compose file or a separate one.
   - Recommendation: Add a `web` service to the existing `docker-compose.yml`. The Next.js container communicates with FastAPI via the Docker network (internal URL `http://api:8000`), not through Nginx.

## Sources

### Primary (HIGH confidence)
- Next.js 16 blog post: https://nextjs.org/blog/next-16 -- version details, proxy.ts, breaking changes
- Next.js proxy documentation: https://nextjs.org/docs/app/getting-started/proxy -- proxy.ts API
- Auth.js Zitadel provider: https://authjs.dev/getting-started/providers/zitadel -- provider config
- Auth.js Next.js reference: https://authjs.dev/reference/nextjs -- auth(), handlers, callbacks
- Auth.js third-party backends guide: https://authjs.dev/guides/integrating-third-party-backends -- token forwarding
- shadcn/ui Sidebar: https://ui.shadcn.com/docs/components/radix/sidebar -- component API
- next-intl App Router setup: https://next-intl.dev/docs/getting-started/app-router/with-i18n-routing -- configuration
- next-intl middleware composition: https://next-intl.dev/docs/routing/middleware -- proxy.ts composition
- Tailwind CSS v4 Next.js guide: https://tailwindcss.com/docs/guides/nextjs -- CSS-first setup
- Zitadel role claims: https://zitadel.com/docs/guides/integrate/retrieve-user-roles -- three settings
- Zitadel OIDC logout: https://zitadel.com/docs/guides/integrate/login/oidc/logout -- end_session_endpoint
- NPM registry: next@16.1.6, next-auth@5.0.0-beta.30, next-intl@4.8.3, tailwindcss@4.2.0, typescript@5.9.3

### Secondary (MEDIUM confidence)
- Zitadel example-auth-nextjs repo: https://github.com/zitadel/example-auth-nextjs -- reference implementation
- CVE-2025-29927 details: https://securitylabs.datadoghq.com/articles/nextjs-middleware-auth-bypass/ -- vulnerability details
- Auth.js + Better Auth announcement: https://github.com/nextauthjs/next-auth/discussions/13252 -- maintenance status

### Tertiary (LOW confidence)
- Auth.js v5 middleware + next-intl composition: https://medium.com/@yokohailemariam/conquering-auth-v5-and-next-intl-middleware-in-next-js-14-app-55f59d40afb4 -- community pattern (Next.js 14, needs adaptation for proxy.ts)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified via npm registry, official docs reviewed
- Architecture: HIGH -- patterns from official docs and Zitadel example repo
- Pitfalls: HIGH -- all 7 critical pitfalls from project research verified with official sources; added 2 more from research
- Auth.js v5 stability: MEDIUM -- beta.30 is production-proven but Auth.js is in maintenance mode; security patches guaranteed
- Proxy composition (auth + i18n): MEDIUM -- pattern verified in next-intl docs but Next.js 16 proxy.ts is new (Oct 2025)

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (30 days -- stack is stable, no major releases expected)

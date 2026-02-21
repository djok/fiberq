# Pitfalls Research

**Domain:** Adding Next.js WebUI to existing FastAPI/Zitadel FTTX management platform
**Researched:** 2026-02-21
**Confidence:** HIGH (verified against official Zitadel docs, Next.js docs, and existing codebase)

## Critical Pitfalls

### Pitfall 1: Audience Mismatch Between Frontend and Backend Tokens

**What goes wrong:**
The existing FastAPI backend validates JWT tokens with `audience=settings.zitadel_client_id` (see `server/api/auth/zitadel.py:89`). When a new Next.js frontend application is created in Zitadel with its own client ID, tokens issued to the frontend will have the frontend's client ID as the audience -- not the backend's. Every API call from the frontend will fail with 401 "Token validation failed" because the backend rejects the audience claim.

**Why it happens:**
Developers create two separate Zitadel applications (one Web/PKCE for Next.js, one API for FastAPI) and assume tokens are interchangeable. In OIDC, the `aud` claim is bound to the client ID of the application that requested the token.

**How to avoid:**
Two viable approaches:

**Option A (recommended): Both apps in same Zitadel project, backend accepts multiple audiences.** Add the scope `urn:zitadel:iam:org:project:id:{projectId}:aud` to the Next.js auth request. This adds the project ID to the token's audience. Then modify `server/api/auth/zitadel.py` to validate against a list of accepted audiences (both the frontend client ID and the backend client ID, or use the project ID as audience).

**Option B: Single Zitadel application used by both.** Both frontend and backend share the same client ID. The frontend uses PKCE (no secret needed), and the backend validates tokens against that same client ID. This is simpler but less flexible if the apps need different scopes.

**Warning signs:**
- After integrating Next.js auth, API calls return 401 even though the user is logged in
- The `/auth/me` endpoint works from Postman with a QGIS-obtained token but fails with a Next.js-obtained token
- JWT decode shows different `aud` claims for tokens from each application

**Phase to address:**
Phase 1 (Auth Integration). This must be the very first thing resolved. Every downstream feature depends on tokens flowing correctly from frontend to backend.

---

### Pitfall 2: CORS Wildcard with Credentials Breaks Cookie-Based Auth

**What goes wrong:**
The existing FastAPI CORS config (`server/api/main.py:41-47`) uses `allow_origins=["*"]` with `allow_credentials=True`. This combination is explicitly prohibited by the CORS specification. Browsers silently reject the `Access-Control-Allow-Origin: *` header when the request includes credentials (cookies, Authorization header with credentials mode). Once the Next.js frontend sends authenticated requests, CORS preflight responses will be rejected.

**Why it happens:**
The current `allow_origins=["*"]` works today because the QGIS desktop client does not enforce CORS (it is not a browser). Developers assume "it works" and do not touch CORS config. The first time a browser-based frontend sends credentialed requests, everything breaks.

**How to avoid:**
Replace the wildcard with explicit origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-production-domain.com",
        "http://localhost:3000",  # Next.js dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If the frontend and backend are served from the same origin via nginx (same domain, no port difference), CORS is not triggered at all for production. But CORS config is still needed for local development where Next.js dev server runs on port 3000 and the API on port 8000.

**Warning signs:**
- Browser console shows "CORS policy: The value of the 'Access-Control-Allow-Origin' header must not be the wildcard '*' when the request's credentials mode is 'include'"
- API requests work from Postman/curl but fail from the browser
- Preflight OPTIONS requests return 200 but the actual request is blocked

**Phase to address:**
Phase 1 (Auth Integration). Fix CORS before any browser-based testing begins.

---

### Pitfall 3: NextAuth JWE Tokens Are Not Standard JWTs -- Backend Cannot Validate Them

**What goes wrong:**
If the Next.js frontend uses NextAuth.js (Auth.js) to manage sessions, NextAuth encrypts its session tokens using JWE (JSON Web Encryption) with AES-256-GCM, not standard signed JWTs. The FastAPI backend uses `python-jose` to decode standard RS256-signed Zitadel JWTs. If developers try to pass the NextAuth session token to the FastAPI backend as a Bearer token, decoding will fail because it is an encrypted blob, not a signed JWT.

**Why it happens:**
Confusion between two distinct tokens: (1) the Zitadel OIDC access token (signed JWT, validated by backend), and (2) the NextAuth session token (encrypted JWE, only meaningful to Next.js). Developers conflate "the token" without understanding there are two separate token lifecycles.

**How to avoid:**
Adopt the **BFF (Backend-for-Frontend) pattern with token forwarding**:

1. Next.js authenticates user via OIDC Authorization Code + PKCE flow with Zitadel
2. The Zitadel access token (standard JWT) is stored in the NextAuth session (server-side, in the JWT callback)
3. When the Next.js frontend calls the FastAPI API, it extracts the Zitadel access token from the session and sends it as `Authorization: Bearer <zitadel_access_token>`
4. FastAPI validates the Zitadel access token using its existing `validate_token()` function -- no changes needed to the backend auth flow

The key is: **never send the NextAuth session token to FastAPI. Always forward the original Zitadel access token.**

In the NextAuth `jwt` callback:
```typescript
async jwt({ token, account }) {
  if (account) {
    token.accessToken = account.access_token;
    token.refreshToken = account.refresh_token;
    token.expiresAt = account.expires_at;
  }
  return token;
}
```

In the NextAuth `session` callback:
```typescript
async session({ session, token }) {
  session.accessToken = token.accessToken;
  return session;
}
```

**Warning signs:**
- FastAPI logs show "Invalid token header" when receiving requests from the frontend
- The token being sent starts with `eyJ` but decodes to an encrypted payload instead of a JSON claims object
- `jwt.get_unverified_header()` raises an exception

**Phase to address:**
Phase 1 (Auth Integration). This is a design decision that must be made before writing any frontend API client code.

---

### Pitfall 4: Zitadel Project Roles Missing from Tokens

**What goes wrong:**
The existing backend extracts roles from `urn:zitadel:iam:org:project:roles` in JWT claims (see `server/api/auth/zitadel.py:107`). After setting up the Next.js OIDC flow, tokens arrive without role claims. The `_extract_roles()` function returns an empty list, and every role-protected endpoint returns 403 Forbidden.

**Why it happens:**
Three independent configuration requirements must ALL be satisfied for roles to appear in tokens:

1. The OIDC scope `urn:zitadel:iam:org:project:roles` must be requested during authentication
2. The Zitadel project setting "Assert Roles on Authentication" must be enabled
3. If roles are needed in the ID token (not just userinfo), the application setting "User Roles Inside ID Token" must be enabled

Missing any single one of these causes roles to be silently absent. The Zitadel docs themselves note this is a common source of confusion (GitHub issue #4828).

**How to avoid:**
In the Next.js OIDC configuration, explicitly request the role scope:

```typescript
authorization: {
  params: {
    scope: "openid profile email urn:zitadel:iam:org:project:roles offline_access"
  }
}
```

In the Zitadel Console:
- Project settings: Enable "Assert Roles on Authentication"
- Application settings: Enable "User Roles Inside ID Token"

Write an integration test that verifies the decoded token contains the `urn:zitadel:iam:org:project:roles` claim before building any role-gated UI.

**Warning signs:**
- User can log in successfully but sees "forbidden" errors everywhere
- `/auth/me` returns `{ roles: [] }` even for users with roles assigned in Zitadel
- The token's claims (when decoded) have no `urn:zitadel:iam:org:project:roles` key

**Phase to address:**
Phase 1 (Auth Integration). Verify role claims flow before building any role-gated UI or permission checks.

---

### Pitfall 5: Role Rename Migration Breaks Both Backend and QGIS Plugin

**What goes wrong:**
The project plans to change roles from `admin, engineer, field_worker` to `Admin, PM, Designer, Field Worker`. The existing backend code has hardcoded role strings in `server/api/auth/roles.py` (`require_role("admin")`, `require_role("admin", "engineer")`, etc.) and in `server/api/dependencies.py`. The QGIS plugin requests scope `urn:zitadel:iam:org:project:roles` and will receive new role names. If roles are renamed in Zitadel without a coordinated migration, both the backend and the existing QGIS plugin break simultaneously.

**Why it happens:**
Zitadel role keys are the authoritative identifiers. Renaming means removing old roles and creating new ones (Zitadel has no "rename role key" operation -- the key IS the identity). The backend role checks are string-equality based. A user with role "Admin" will not pass `require_role("admin")`.

**How to avoid:**
Execute a phased migration:

1. **Phase 1:** Create new roles in Zitadel alongside old ones. Assign users to both old and new roles.
2. **Phase 2:** Update the backend `_extract_roles()` to map/normalize both formats:
   ```python
   ROLE_ALIASES = {
       "Admin": "admin",
       "PM": "engineer",
       "Designer": "engineer",
       "Field Worker": "field_worker",
   }
   ```
3. **Phase 3:** Deploy updated backend and new frontend simultaneously.
4. **Phase 4:** After confirming QGIS plugin is updated, remove old role assignments.

Never delete old roles before both the backend and ALL clients (QGIS plugin included) support the new role names.

**Warning signs:**
- Users report "forbidden" errors after role changes
- Some users can access features and others cannot, with no clear pattern
- QGIS plugin users suddenly lose access while web users work fine (or vice versa)

**Phase to address:**
Phase 1 (Auth Integration) for the mapping layer, but actual role cutover should be a dedicated migration phase after both clients are deployed.

---

### Pitfall 6: SSR Token Access -- Server Components Cannot Read Client-Side Auth State

**What goes wrong:**
Developers build the Next.js frontend using React Server Components (RSCs) and attempt to fetch data from FastAPI during server-side rendering. But the Zitadel access token is only available in the client's session/cookie. If the token is stored in client-side state (e.g., React context or localStorage), Server Components cannot access it at all. The page either renders without data or throws 401 errors during SSR.

**Why it happens:**
Next.js App Router heavily promotes Server Components as the default. Developers write `async function Page()` components that fetch data during SSR, but forget that authentication tokens must be explicitly forwarded from the incoming request cookies through to the API call.

**How to avoid:**
Use NextAuth's server-side session retrieval in Server Components:

```typescript
import { auth } from "@/auth";

export default async function Page() {
  const session = await auth();  // reads from cookie on server
  const data = await fetch("http://api:8000/projects", {
    headers: { Authorization: `Bearer ${session?.accessToken}` }
  });
  // ...
}
```

Key architectural decisions:
- Store the Zitadel access token in the NextAuth session (JWT strategy)
- Use `auth()` in Server Components to retrieve the token server-side
- For client components that need to call the API, expose the token via a session provider or use Next.js API routes as a proxy (BFF pattern)

**Warning signs:**
- Pages render correctly when navigated to client-side but show "unauthorized" or empty data on hard refresh
- SSR logs show 401 errors from the FastAPI backend
- `getServerSession()` / `auth()` returns null in Server Components

**Phase to address:**
Phase 1 (Auth Integration) -- architecture decision. Phase 2 (Core Pages) -- implementation.

---

### Pitfall 7: Nginx Routing Conflict Between Next.js and FastAPI

**What goes wrong:**
The existing nginx config (`server/nginx/nginx.conf`) routes `/api/*` to FastAPI and `/` (catch-all) to static HTML. Adding Next.js requires routing `/_next/*` (static assets, webpack chunks), Next.js page routes, and potentially `/api/auth/*` (NextAuth callbacks) -- which conflicts with the existing `/api/` location that proxies to FastAPI.

Specifically: NextAuth callback URLs default to `/api/auth/callback/zitadel`, which matches the existing `/api/` location block and gets routed to FastAPI instead of Next.js. FastAPI returns 404, and OIDC login breaks.

**Why it happens:**
nginx location matching uses longest prefix match. `/api/` matches `/api/auth/callback/zitadel`, so it goes to FastAPI. Developers add a Next.js upstream but forget that NextAuth's default routes conflict with the existing API prefix.

**How to avoid:**
Two options:

**Option A (recommended): Move NextAuth routes out of /api/.** Configure NextAuth with a custom `basePath`:
```typescript
// auth.ts
export const { handlers, auth } = NextAuth({
  // ...
  basePath: "/auth",  // NOT /api/auth
})
```
This avoids all conflict with the `/api/` prefix.

**Option B: Add specific nginx location blocks for NextAuth routes.**
```nginx
# NextAuth callbacks -- MUST come before /api/
location /api/auth/ {
    proxy_pass http://nextjs:3000;
}

# FastAPI backend
location /api/ {
    proxy_pass http://api:8000/;
}

# Next.js frontend (everything else)
location / {
    proxy_pass http://nextjs:3000;
}
```
nginx uses longest prefix match, so `/api/auth/` is more specific than `/api/` and will match first.

Also: the `/_next/` path must route to Next.js, not to the static HTML fallback.

**Warning signs:**
- OIDC login redirects result in 404 or unexpected JSON responses from FastAPI
- Next.js pages load but CSS/JS assets return 404
- Hot Module Replacement (HMR) fails in development because `/_next/webpack-hmr` WebSocket is not proxied

**Phase to address:**
Phase 1 (Infrastructure Setup). Nginx routing must be configured before any frontend pages can be tested.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `allow_origins=["*"]` for CORS | Works immediately, no config needed | Blocks credentialed requests from browsers; security vulnerability in production | Never in production. Acceptable only for initial local API testing with curl/Postman |
| Storing access token in localStorage | Simple client-side token access | XSS vulnerability exposes tokens; not accessible in Server Components; no auto-refresh | Never. Use httpOnly cookies via NextAuth session |
| Skipping token refresh in NextAuth | Simpler auth setup | Users get logged out after token expiry (default 1 hour with Zitadel); bad UX for long sessions | Only for initial prototype; must implement before user testing |
| Hardcoding role strings without a mapping layer | Quick to implement | Role renames require changes in every file that checks roles; fragile when adding new roles | Only if roles are truly final and will never change |
| Using Next.js `output: 'export'` (static export) | No Node.js runtime needed in Docker | Loses SSR, middleware, API routes, server components; must re-add a runtime later for auth | Never for this project -- auth requires server-side rendering |
| Duplicating API types manually (no shared schema) | Works immediately | Types drift between FastAPI Pydantic models and TypeScript interfaces; silent bugs | Only for first 2-3 endpoints. Generate types from OpenAPI spec thereafter |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Zitadel OIDC | Requesting `openid profile email` scope without `urn:zitadel:iam:org:project:roles` -- roles silently missing from token | Always include `urn:zitadel:iam:org:project:roles` and `offline_access` in scope. Verify with token decode before building features |
| Zitadel OIDC | Not enabling "Assert Roles on Authentication" in project settings | Check project settings AND application settings in Zitadel Console. Both must be configured |
| Zitadel OIDC | Using Implicit flow for the web app | Use Authorization Code + PKCE. Zitadel recommends this explicitly. Implicit flow is deprecated for web apps |
| NextAuth + Zitadel | Assuming NextAuth auto-discovers all Zitadel endpoints | Verify the issuer URL includes the protocol (`https://your-domain.zitadel.cloud`). NextAuth uses `.well-known/openid-configuration` which must be accessible from the Next.js server container |
| NextAuth + Zitadel | Forgetting to configure post-logout redirect URI in Zitadel | Logout appears to work but user is not actually logged out of Zitadel. They auto-login again on next visit without seeing a login screen |
| FastAPI + Next.js | Calling FastAPI from Next.js Server Components using `localhost:8000` | In Docker, use the service name (`http://api:8000`). `localhost` from the Next.js container refers to the Next.js container itself, not the FastAPI container |
| Nginx + Next.js | Serving `/_next/static/` files through nginx `try_files` instead of proxying to Next.js | The `/_next/` path contains dynamically generated assets. Proxy all `/_next/` requests to the Next.js server instead of trying to serve them as static files |
| Cloudflare Tunnel | Not accounting for Cloudflare stripping/modifying headers | Ensure `X-Forwarded-Proto` and `X-Forwarded-Host` are correctly passed through. NextAuth uses these for callback URL construction |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching all GeoJSON features on page load without pagination | Works with 10 features, page hangs with 10,000 | Implement bbox-based spatial queries; use vector tiles for map display; paginate table views | > 1,000 features per layer |
| Calling Zitadel JWKS endpoint on every request | Invisible at low traffic, adds 50-200ms latency per request | The existing backend caches JWKS but never invalidates the cache on a schedule. Add TTL-based cache refresh (e.g., every 5 minutes) instead of caching forever or refetching every time | > 50 concurrent users |
| Server-side rendering every page on every request | Low TTFB with few users | Use ISR (Incremental Static Regeneration) for read-heavy pages like project lists. Use `revalidate` with appropriate intervals | > 20 concurrent page loads |
| Loading full PostGIS geometry in API responses when only summary data is needed | Works fine with simple geometries | Return simplified geometries or omit `geom` from list endpoints; load full geometry only for detail/edit views | > 100 features with complex LineString/Polygon geometries |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Relying only on Next.js middleware for auth checks (CVE-2025-29927) | Critical: Middleware can be bypassed by setting `x-middleware-subrequest` header. Attacker accesses protected pages without login | Strip `x-middleware-subrequest` header in nginx. Always validate auth on the API layer (FastAPI), not just the UI layer. Update Next.js to >= 15.2.3. The existing FastAPI auth is the true security boundary |
| Exposing the Zitadel client secret in client-side code | Token theft, account impersonation | Use PKCE flow (no client secret in browser). Store secrets only in server-side `.env`. The QGIS plugin already uses Device Flow (no secret) -- the web app should use PKCE (no secret in browser) |
| Not validating `state` parameter in OIDC callback | CSRF attacks on login flow | NextAuth handles this automatically if configured correctly. Do not implement custom OIDC callback handling |
| Serving the `_next/data/` routes without auth on SSR pages that contain sensitive data | Data leakage: `_next/data/` JSON payloads contain the same data as the rendered page but as raw JSON | Ensure middleware protects `_next/data/` paths alongside page paths. Or use Server Components (RSC payload is not as easily scraped) |
| Storing Zitadel project ID or internal API keys in `next.config.js` (client-side bundle) | Keys exposed in browser source | Use `NEXT_PUBLIC_` prefix ONLY for non-sensitive values (like the Zitadel domain for login redirect). Keep secrets in server-only env vars (no `NEXT_PUBLIC_` prefix) |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing a blank page during OIDC redirect (login) | Users think the app is broken; they click back/refresh and break the auth flow | Show a loading spinner with "Redirecting to login..." message. Handle the redirect gracefully in middleware |
| Not handling token expiry on long-idle sessions | User fills out a complex work order form, submits, gets 401, loses all input | Implement proactive token refresh in middleware. For forms: save draft to localStorage, detect 401, re-authenticate, re-submit |
| Showing "403 Forbidden" as raw text for missing roles | Non-technical field workers are confused | Show friendly messages: "You don't have permission to access this feature. Contact your administrator." Include the user's current role and what role is needed |
| Map page loads slowly due to SSR of GeoJSON data | 3-5 second blank screen before map appears | Render map client-side (CSR) with a loading skeleton. The map library (Leaflet/MapLibre) must run in the browser anyway. SSR the page layout, hydrate the map client-side |
| Forcing desktop-optimized views on field workers using phones | Field workers cannot use the app effectively in the field | Design field-worker-facing pages (work orders, photo upload, SMR reports) mobile-first. Use responsive breakpoints. Consider separate route groups for field vs. office views |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **OIDC Login:** Login works, but refresh token is not stored -- user will be logged out after 1 hour. Verify `offline_access` scope and refresh token persistence in NextAuth JWT callback
- [ ] **OIDC Logout:** Clicking "logout" clears the local session but does NOT end the Zitadel session. User clicks "login" and auto-logs in without seeing the Zitadel login screen. Verify federated logout via end-session endpoint
- [ ] **Role-based UI:** Role checks hide UI elements, but API endpoints are not protected. A user can access data by calling the API directly. Verify FastAPI `Depends(require_admin)` is on every sensitive endpoint
- [ ] **Nginx config:** Frontend pages load, but `/_next/static/` chunks return 404 on hard refresh because nginx `try_files` catches them before the Next.js proxy. Verify all `/_next/` paths proxy to Next.js
- [ ] **Docker networking:** API calls work in development (direct to localhost:8000) but fail in Docker because Server Components call `localhost` which resolves to the Next.js container, not FastAPI. Verify using Docker service names in server-side fetch URLs
- [ ] **CORS:** Works in dev because same-origin via proxy. Breaks in staging/production where domains differ. Verify CORS config with actual production domain
- [ ] **Map component:** Map renders, but WebSocket for HMR is not proxied through nginx -- every hot reload requires full page refresh in dev. Verify `/_next/webpack-hmr` WebSocket upgrade in nginx dev config
- [ ] **Token in SSR:** Pages render correctly on client-side navigation but show empty/error state on full page reload (SSR) because the token is not read from cookies during server render

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Audience mismatch (Pitfall 1) | LOW | Change Zitadel app config or add audience scope. Update one line in backend token validation. No data loss |
| CORS wildcard (Pitfall 2) | LOW | Update 3 lines in `main.py` CORS config. Redeploy. No data loss |
| NextAuth JWE confusion (Pitfall 3) | MEDIUM | If caught early (Phase 1), refactor auth client code. If caught after many components are built, need to update every API call to use the correct token |
| Missing roles in token (Pitfall 4) | LOW | Fix Zitadel project/app settings and OIDC scope. No code changes if role extraction already checks the right claim key |
| Role rename without migration (Pitfall 5) | HIGH | Must retroactively assign old+new roles to all users, update backend role checks, deploy hotfix. Extended downtime for QGIS users if they cannot authenticate |
| SSR token unavailable (Pitfall 6) | MEDIUM-HIGH | Architectural change from client-side auth to server-side session. May require rewriting page components that fetch data |
| Nginx routing conflict (Pitfall 7) | LOW | Adjust nginx location blocks. Possibly change NextAuth basePath. No data loss |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Audience mismatch | Phase 1: Auth Integration | Decode a frontend-obtained token and confirm `aud` claim is accepted by FastAPI `validate_token()`. Automated test: call `/auth/me` with a frontend token |
| CORS wildcard | Phase 1: Auth Integration | From a browser on the production domain, make a credentialed fetch to `/api/health`. Confirm `Access-Control-Allow-Origin` is the correct origin, not `*` |
| NextAuth JWE vs Zitadel JWT | Phase 1: Auth Integration | Log the `Authorization` header received by FastAPI. Confirm it is a valid Zitadel RS256 JWT, not a NextAuth JWE blob |
| Missing roles | Phase 1: Auth Integration | Automated test: authenticate as a user with known roles, call `/auth/roles`, verify roles array matches Zitadel assignment |
| Role rename breakage | Phase 1 (mapping layer), Phase 3 (cutover) | Dual-role test: assign user both old and new roles, verify both backend and QGIS plugin work. Then remove old roles and verify only new roles work with updated code |
| SSR token access | Phase 1 (architecture), Phase 2 (pages) | Load a protected page via hard refresh (SSR). Confirm it renders with data, not a 401 fallback. Check Next.js server logs for successful FastAPI calls during render |
| Nginx routing conflict | Phase 1: Infrastructure | Automated smoke test: `curl /api/auth/callback/zitadel` returns NextAuth response (not FastAPI 404). `curl /api/projects` returns FastAPI response. `curl /_next/static/[chunk]` returns JavaScript |

## Sources

- [Zitadel: Retrieve User Roles](https://zitadel.com/docs/guides/integrate/retrieve-user-roles) -- role scopes and project settings (HIGH confidence)
- [Zitadel: OIDC Scopes](https://zitadel.com/docs/apis/openidoauth/scopes) -- exact scope strings for project roles (HIGH confidence)
- [Zitadel: Recommended OAuth Flows](https://zitadel.com/docs/guides/integrate/login/oidc/oauth-recommended-flows) -- PKCE for web apps (HIGH confidence)
- [Zitadel: Next.js SDK Examples](https://zitadel.com/docs/sdk-examples/nextjs) -- NextAuth + Zitadel integration (HIGH confidence)
- [Zitadel GitHub: example-auth-nextjs](https://github.com/zitadel/example-auth-nextjs) -- reference implementation (HIGH confidence)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/) -- wildcard + credentials restriction (HIGH confidence)
- [CVE-2025-29927: Next.js Middleware Bypass](https://securitylabs.datadoghq.com/articles/nextjs-middleware-auth-bypass/) -- critical security vulnerability (HIGH confidence)
- [Combining NextAuth with FastAPI](https://tom.catshoek.dev/posts/nextauth-fastapi/) -- JWE token format and decryption approach (MEDIUM confidence)
- [NextAuth.js: Accessing access_token in Server Components](https://github.com/nextauthjs/next-auth/issues/7913) -- SSR token forwarding (MEDIUM confidence)
- [Next.js: basePath with nginx reverse proxy](https://github.com/vercel/next.js/issues/8172) -- static asset 404 issues (MEDIUM confidence)
- [Zitadel GitHub Discussion #4828](https://github.com/zitadel/zitadel/issues/4828) -- role scope documentation confusion (MEDIUM confidence)
- [Zitadel GitHub Discussion #5829](https://github.com/zitadel/zitadel/discussions/5829) -- reserved scopes not returning results (MEDIUM confidence)
- Existing codebase analysis: `server/api/auth/zitadel.py`, `server/api/main.py`, `server/nginx/nginx.conf` (HIGH confidence -- direct inspection)

---
*Pitfalls research for: Next.js WebUI addition to existing FastAPI/Zitadel FTTX management platform*
*Researched: 2026-02-21*

---
milestone: v1
audited: 2026-02-22
status: tech_debt
scores:
  requirements: 22/22
  phases: 3/4 verified (Phase 1 missing VERIFICATION.md)
  integration: 22/23 connections wired
  flows: 4/4 E2E flows functional (1 with gap)
gaps: []
tech_debt:
  - phase: 01-auth-foundation-app-shell
    items:
      - "Missing VERIFICATION.md — phase verified only via build/TypeScript checks in SUMMARYs"
      - "proxy.ts not loaded as Next.js middleware (named proxy.ts, not middleware.ts) — auth mitigated by layout-level checks"
      - "server/api/dependencies.py is dead code — orphaned by auth/roles.py which provides same functionality"
  - phase: 02-user-management
    items:
      - "No items — phase clean"
  - phase: 03-project-management-assignment
    items:
      - "DELETE /api/projects/{id} endpoint exists but has no frontend consumer (no delete button/dialog in UI)"
      - "Assignable users list sourced from user_logins, not Kanidm — newly created users not assignable until first login"
  - phase: 04-dashboard-analytics
    items:
      - "dashboard/page.tsx has no explicit auth() check (protected by layout guard but deviates from per-page pattern)"
---

# Milestone v1 Audit Report

**Milestone:** FiberQ WebUI v1
**Audited:** 2026-02-22
**Status:** TECH DEBT (all requirements met, no critical blockers, accumulated debt)

---

## Executive Summary

All 22 v1 requirements are satisfied. Four phases completed with 11 plans executed. Cross-phase integration is solid — 22 of 23 tracked connections are properly wired. All 4 E2E user flows are functional (1 with a minor gap). No critical blockers exist. Six tech debt items accumulated across 3 phases need review before archiving.

---

## Requirements Coverage

### Authentication & Session (Phase 1)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **AUTH-01**: User can log in via OIDC (PKCE flow with Auth.js v5) | SATISFIED | auth.ts with custom Kanidm OIDC provider, PKCE S256, tested via curl |
| **AUTH-02**: Session persists across refresh with silent token renewal | SATISFIED | auth.ts JWT callback with expiresAt check and token refresh logic |
| **AUTH-03**: User can log out from any page | SATISFIED | signOut({ redirectTo: "/" }) in user-nav.tsx (Kanidm lacks end_session_endpoint) |
| **AUTH-04**: User can view profile page (name, email, role) | SATISFIED | /[locale]/profile/page.tsx with profile-card.tsx showing Kanidm token claims |

### User Management (Phase 2)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **USER-01**: Admin can view list of all users | SATISFIED | GET /api/users returns Kanidm persons with name, email, role, status, last login |
| **USER-02**: Admin can create new user with role | SATISFIED | POST /api/users creates Kanidm person, assigns groups, returns credential reset token |
| **USER-03**: Admin can deactivate/reactivate user | SATISFIED | POST /api/users/{id}/deactivate sets account_expire; /reactivate clears it |
| **USER-04**: Admin can change user role | SATISFIED | PUT /api/users/{id}/roles replaces fiberq_* group memberships |
| **USER-05**: Admin can trigger password reset | SATISFIED | POST /api/users/{id}/reset-password returns credential reset token |
| **USER-06**: Admin can see last login timestamp | SATISFIED | user_logins table populated on sign-in, displayed in user list and detail |

### Project Management (Phase 3)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **PROJ-01**: User sees only assigned projects (admin sees all) | SATISFIED | Role-scoped SQL in list endpoint, 403 guard in detail endpoint |
| **PROJ-02**: Admin/PM can create project | SATISFIED | POST /projects with require_project_manager_or_admin, frontend create dialog |
| **PROJ-03**: Admin/PM can edit project | SATISFIED | PUT /projects/{id} with edit dialog, status change logged to activity |
| **PROJ-04**: Projects have status lifecycle | SATISFIED | Status column with 5 states (planning/design/construction/as-built/completed) |
| **PROJ-05**: User can filter/search projects | SATISFIED | Three client-side filters: name search, status dropdown, user dropdown |

### Project-User Assignment (Phase 3)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **ASGN-01**: Admin/PM can assign users to project | SATISFIED | POST /projects/{id}/members with combobox UI and role selection |
| **ASGN-02**: User can view project members | SATISFIED | Members list with initials avatar, name, email, role badge |
| **ASGN-03**: Admin/PM can remove user from project | SATISFIED | DELETE /projects/{id}/members/{user_sub} with confirmation dialog |

### UI/UX (Phase 1)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **UIUX-01**: Navigation adapts based on user role | SATISFIED | filterNavByRole hides Users link for non-admins, sidebar-nav.tsx |
| **UIUX-02**: Responsive layout usable on 768px viewport | SATISFIED | Collapsible sidebar (icons-only on tablet), Sheet on mobile |

### Dashboard & Analytics (Phase 4)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **DASH-01**: Project detail shows element counts, team size, last sync | SATISFIED | GET /projects/{id}/stats with 6 stat tiles (closures, poles, cables, cable length, team, last sync) |
| **DASH-02**: Project detail shows activity feed | SATISFIED | GET /projects/{id}/activity with UNION ALL, day-grouped timeline, load-more pagination |

**Score: 22/22 requirements satisfied**

---

## Phase Verification Status

| Phase | VERIFICATION.md | Status | Score |
|-------|-----------------|--------|-------|
| 1. Auth Foundation & App Shell | MISSING | Unverified (build/TS checks only) | N/A |
| 2. User Management | Present | PASSED | 14/14 |
| 3. Project Management & Assignment | Present | PASSED | 5/5 |
| 4. Dashboard & Analytics | Present | PASSED | 9/9 |

**Phase 1 Note:** Phase 1 has 3 SUMMARY.md files confirming TypeScript compilation, npm build success, and curl-tested OIDC flow. However, no formal VERIFICATION.md was generated by the gsd-verifier. The phase was the first executed and predates the verification workflow.

---

## Cross-Phase Integration

### Wiring Status

| Connection | From | To | Status |
|------------|------|----|--------|
| Auth dependency → User endpoints | Phase 1 auth/roles.py | Phase 2 routes.py | WIRED |
| Auth dependency → Project endpoints | Phase 1 auth/kanidm.py | Phase 3 routes.py | WIRED |
| apiFetch token forwarding → All pages | Phase 1 api.ts | All server actions | WIRED |
| Login tracking → User list | Phase 1 auth.ts → user_logins | Phase 2 user list | WIRED |
| Role filtering → Sidebar nav | Phase 1 roles.ts | sidebar-nav.tsx | WIRED |
| Users router → main.py | Phase 2 routes.py | Phase 1 main.py | WIRED |
| Projects router → main.py | Phase 3 routes.py | Phase 1 main.py | WIRED |
| User data → Assignable users | Phase 2 user_logins | Phase 3 combobox | WIRED (gap noted) |
| Project detail → Stats | Phase 3 detail page | Phase 4 stats endpoint | WIRED |
| Project detail → Activity | Phase 3 detail page | Phase 4 activity endpoint | WIRED |
| Mutations → Activity log | Phase 3 update/remove | Phase 4 activity_log table | WIRED |

**Orphaned:**
- `server/api/dependencies.py` — entire file unused (superseded by `auth/roles.py`)

### E2E Flows

| Flow | Status | Notes |
|------|--------|-------|
| Admin full flow (login → users → projects → assign → dashboard) | COMPLETE | All steps connected |
| Non-admin flow (login → limited nav → assigned projects → detail) | COMPLETE | Role filtering works at nav, page, and API levels |
| User lifecycle (create → assign → deactivate) | COMPLETE with GAP | Newly created users not assignable until first login |
| Project lifecycle (create → edit → assign → stats → activity) | COMPLETE | Status changes and member removals logged to activity feed |

---

## Tech Debt Summary

### Phase 1: Auth Foundation & App Shell

| # | Item | Severity | Impact |
|---|------|----------|--------|
| 1 | Missing VERIFICATION.md | Low | No formal verification report; phase validated via summaries and build checks |
| 2 | `proxy.ts` not loaded as middleware | Medium | Named `proxy.ts` instead of `middleware.ts`; Next.js ignores it. Auth still enforced at layout level. Root `/` URL behavior affected. |
| 3 | `dependencies.py` dead code | Low | Orphaned file with duplicate role-check functions; `auth/roles.py` is the active implementation |

### Phase 3: Project Management & Assignment

| # | Item | Severity | Impact |
|---|------|----------|--------|
| 4 | DELETE /projects/{id} has no frontend consumer | Low | Backend endpoint exists but no UI delete button. Projects cannot be deleted from WebUI. |
| 5 | Assignable users sourced from user_logins only | Medium | Users created by admin not assignable until their first login. Workaround: tell user to log in first. |

### Phase 4: Dashboard & Analytics

| # | Item | Severity | Impact |
|---|------|----------|--------|
| 6 | `dashboard/page.tsx` missing explicit auth check | Low | Protected by locale layout guard; deviates from per-page auth pattern used in all other pages |

**Total: 6 items across 3 phases (2 medium, 4 low)**

---

## Integration Checker Notes

- **Trailing slash inconsistency:** Users router uses `@router.get("")` while Projects router uses `@router.get("/")`. FastAPI's `redirect_slashes=True` handles this but adds a redirect round-trip for project list/create operations.
- **All 15 consumed API routes** have frontend callers via `apiFetch()`. No raw `fetch()` calls bypass the token forwarding pattern.
- **CORS protection** uses explicit origins (not wildcard) in `main.py`.
- **Kanidm migration** from Zitadel is complete — zero Zitadel references remain in codebase.

---

*Audited: 2026-02-22*
*Auditor: Claude (gsd audit-milestone)*

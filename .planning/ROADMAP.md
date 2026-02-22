# Roadmap: FiberQ WebUI

## Overview

FiberQ WebUI transforms an existing QGIS-only fiber optic management system into a browser-accessible platform. The journey starts with solving the hardest problem first -- authentication integration between Next.js, Kanidm, and FastAPI (where all 7 critical pitfalls live). Once tokens flow correctly, we build the two features that justify the WebUI's existence: user lifecycle management (without the Kanidm console) and project-to-user assignment (without raw API calls). Finally, dashboard views aggregate existing data into actionable project intelligence.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Auth Foundation & App Shell** - OIDC login, session management, role-based navigation shell, responsive layout, Docker integration
- [x] **Phase 2: User Management** - Admin CRUD for user accounts via Kanidm Management API
- [x] **Phase 3: Project Management & Assignment** - Project CRUD, user-to-project assignment with new junction table
- [x] **Phase 4: Dashboard & Analytics** - Per-project stats and activity feed over existing data
- [ ] **Phase 5: Tech Debt Cleanup** - Middleware fix, dead code removal, assignable users fix, project delete UI, auth consistency

## Phase Details

### Phase 1: Auth Foundation & App Shell
**Goal**: Users can securely log in to a working Next.js application that enforces role-based access and renders correctly on tablets
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, UIUX-01, UIUX-02
**Success Criteria** (what must be TRUE):
  1. User can log in via Kanidm OIDC in a browser, and a hard-refresh of a protected page renders with data (not a 401 or login redirect)
  2. User can log out from any page and is redirected to the login screen with Kanidm session ended
  3. User can view their own profile page showing name, email, and role (sourced from Kanidm token claims)
  4. An Admin user sees the "User Management" navigation item; a Field Worker user does not
  5. The application layout renders correctly and is usable on a 768px-wide viewport (tablet)
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md -- Bootstrap Next.js 16 project, Auth.js + Kanidm integration, infrastructure updates (Nginx, CORS, Docker)
- [x] 01-02-PLAN.md -- App shell with collapsible sidebar, role-based navigation, green/teal theme, dark mode, BG/EN bilingual
- [x] 01-03-PLAN.md -- Profile page, placeholder pages, federated logout, end-to-end verification

### Phase 2: User Management
**Goal**: Admins can manage the full user lifecycle from the WebUI without touching the Kanidm console
**Depends on**: Phase 1
**Requirements**: USER-01, USER-02, USER-03, USER-04, USER-05, USER-06
**Success Criteria** (what must be TRUE):
  1. Admin can view a list of all users showing name, email, role, active/inactive status, and last login timestamp
  2. Admin can create a new user with a role assignment, and that user can subsequently log in via Kanidm
  3. Admin can deactivate a user, and that user can no longer log in; admin can reactivate the user and login works again
  4. Admin can change a user's role, and the user's next login reflects the new role in their token claims
  5. Admin can trigger a password reset email for a user
**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md -- FastAPI backend: Kanidm admin client, /users router, last login tracking
- [x] 02-02-PLAN.md -- User list page with data table, search/filters, create user dialog
- [x] 02-03-PLAN.md -- User detail page, actions dropdown, role editing, password reset

### Phase 3: Project Management & Assignment
**Goal**: Users can manage projects and assign team members, with visibility scoped by role and assignment
**Depends on**: Phase 2
**Requirements**: PROJ-01, PROJ-02, PROJ-03, PROJ-04, PROJ-05, ASGN-01, ASGN-02, ASGN-03
**Success Criteria** (what must be TRUE):
  1. A non-admin user sees only projects they are assigned to; an admin sees all projects
  2. Admin or Project Manager can create a project with name and description, and it appears in the project list
  3. Admin or Project Manager can assign a user to a project, and that user then sees the project in their list
  4. User can view the members assigned to a project with their names and roles
  5. User can filter and search projects by name, status, and assigned user
**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md -- Backend: project_users table, status column, role-scoped API, assignment endpoints, PostGIS extent
- [x] 03-02-PLAN.md -- Project list page with card grid, PostGIS mini-maps, filters, create project dialog
- [x] 03-03-PLAN.md -- Project detail page with interactive map, member list, inline assignment combobox, edit dialog

### Phase 4: Dashboard & Analytics
**Goal**: Project detail pages provide at-a-glance intelligence about project health and recent activity
**Depends on**: Phase 3
**Requirements**: DASH-01, DASH-02
**Success Criteria** (what must be TRUE):
  1. Project detail page displays element counts (closures, poles, cables), team size, and last sync timestamp from existing database tables
  2. Project detail page shows an activity feed of recent actions (sync uploads, user assignments, status changes) in reverse chronological order
**Plans:** 2 plans

Plans:
- [x] 04-01-PLAN.md -- Backend: project_activity_log table, stats endpoint, activity feed endpoint, activity logging in mutations
- [x] 04-02-PLAN.md -- Frontend: stat tiles, activity timeline, page restructure, i18n

### Phase 5: Tech Debt Cleanup
**Goal**: Close all tech debt items identified in the v1 milestone audit — fix middleware loading, clean dead code, improve assignable users, add missing UI and auth patterns
**Depends on**: Phase 4
**Requirements**: None (tech debt closure, no new requirements)
**Gap Closure**: Closes 5 tech debt items from v1-MILESTONE-AUDIT.md
**Success Criteria** (what must be TRUE):
  1. Next.js middleware executes at Edge level (proxy.ts renamed to middleware.ts), protecting all routes before layout rendering
  2. Assignable users list includes all Kanidm persons, not just those who have logged in
  3. `server/api/dependencies.py` is deleted (dead code removed)
  4. `dashboard/page.tsx` has an explicit `auth()` check matching per-page pattern
  5. Admin/PM can delete a project from the project detail page with confirmation dialog
**Plans:** 2 plans

Plans:
- [ ] 05-01-PLAN.md -- Middleware rename, dead code removal, dashboard auth check
- [ ] 05-02-PLAN.md -- Assignable users from Kanidm, project delete UI with confirmation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth Foundation & App Shell | 3/3 | Complete | 2026-02-21 |
| 2. User Management | 3/3 | Complete | 2026-02-21 |
| 3. Project Management & Assignment | 3/3 | Complete | 2026-02-22 |
| 4. Dashboard & Analytics | 2/2 | Complete | 2026-02-22 |
| 5. Tech Debt Cleanup | 0/2 | Not started | - |

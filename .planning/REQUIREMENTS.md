# Requirements: FiberQ WebUI

**Defined:** 2026-02-21
**Core Value:** Потребителите могат да се логнат в единна система (Zitadel), да управляват проекти и да работят с оптични мрежи — както от QGIS, така и от уеб браузър.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication & Session

- [ ] **AUTH-01**: User can log in to WebUI via Zitadel OIDC (PKCE flow with Auth.js v5)
- [ ] **AUTH-02**: User session persists across browser refresh with silent token renewal
- [ ] **AUTH-03**: User can log out from any page (clear session + Zitadel end session redirect)
- [ ] **AUTH-04**: User can view own profile page showing name, email, and role (read-only from Zitadel)

### User Management

- [ ] **USER-01**: Admin can view list of all users with name, email, role, and active/inactive status
- [ ] **USER-02**: Admin can create new user with role assignment via Zitadel Management API
- [ ] **USER-03**: Admin can deactivate and reactivate a user account
- [ ] **USER-04**: Admin can change a user's role without recreating the account
- [ ] **USER-05**: Admin can trigger password reset email for a user
- [ ] **USER-06**: Admin can see last login timestamp for each user

### Project Management

- [ ] **PROJ-01**: User can view list of projects they are assigned to (admin sees all projects)
- [ ] **PROJ-02**: Admin or Project Manager can create a new project with name and description
- [ ] **PROJ-03**: Admin or Project Manager can edit project name and description
- [ ] **PROJ-04**: Projects have a status field with lifecycle states (Planning, Design, Construction, As-Built, Completed)
- [ ] **PROJ-05**: User can filter and search projects by name, status, and assigned user

### Project-User Assignment

- [ ] **ASGN-01**: Admin or Project Manager can assign users to a project (new project_users table)
- [ ] **ASGN-02**: User can view list of members assigned to a project with name and role
- [ ] **ASGN-03**: Admin or Project Manager can remove a user from a project

### UI/UX

- [ ] **UIUX-01**: Navigation and visible features adapt based on user role (Admin sees user management; Field Worker does not)
- [ ] **UIUX-02**: WebUI layout is responsive and usable on tablets (min 768px viewport)

### Dashboard & Analytics

- [ ] **DASH-01**: Project detail page shows dashboard with element counts, team size, last sync timestamp
- [ ] **DASH-02**: Project detail page shows activity feed of recent actions (sync uploads, user assignments, status changes)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Project-User Assignment

- **ASGN-04**: Admin can bulk-assign multiple users to a project in one action

### User Onboarding

- **ONBR-01**: Admin can create user with pre-selected role and project assignment in single wizard flow

### Reporting & Export

- **REPT-01**: Admin can export project summary as PDF or CSV (metadata + team + element counts)

### Notifications

- **NOTF-01**: User receives email notification when assigned to a project

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Full user profile editing in WebUI | Zitadel is source of truth for identity data; display read-only only |
| Custom per-project permission matrix | 4 fixed roles is sufficient; per-project overrides add massive complexity |
| Real-time collaborative editing | Design work happens in QGIS, not the web |
| Built-in chat / messaging | Users have existing communication tools (Viber, Telegram, Teams) |
| Multi-tenancy / organization management | FiberQ is single-organization; Zitadel handles multi-org at IdP level |
| Kanban / Gantt project views | FiberQ projects are fiber network scopes, not task-driven project plans |
| Map-based network visualization | Next milestone; requires full GIS rendering capability |
| Project area map preview | Next milestone; requires map library integration (Leaflet/MapLibre) |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | — | Pending |
| AUTH-02 | — | Pending |
| AUTH-03 | — | Pending |
| AUTH-04 | — | Pending |
| USER-01 | — | Pending |
| USER-02 | — | Pending |
| USER-03 | — | Pending |
| USER-04 | — | Pending |
| USER-05 | — | Pending |
| USER-06 | — | Pending |
| PROJ-01 | — | Pending |
| PROJ-02 | — | Pending |
| PROJ-03 | — | Pending |
| PROJ-04 | — | Pending |
| PROJ-05 | — | Pending |
| ASGN-01 | — | Pending |
| ASGN-02 | — | Pending |
| ASGN-03 | — | Pending |
| UIUX-01 | — | Pending |
| UIUX-02 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 0
- Unmapped: 22 (pending roadmap creation)

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-21 after initial definition*

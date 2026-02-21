# Feature Research

**Domain:** FTTX/Fiber Optic Network Management -- WebUI Admin & Project Management
**Researched:** 2026-02-21
**Confidence:** MEDIUM-HIGH

This research covers features for the WebUI layer being added to an existing FTTX management system (FiberQ). The existing system has a FastAPI backend, Zitadel OIDC auth with 3 roles, QGIS plugin for network design, and QField for field data collection. The WebUI adds user management, project management, and a dashboard -- administrative functions that don't belong in a GIS desktop client.

Context: The target roles are Admin, Project Manager, Designer, Field Worker. The system is niche (fiber optic network design/construction), not a mass-market SaaS. User counts are small (tens to low hundreds). The WebUI is the administrative complement to the QGIS design tool.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Missing any of these makes the WebUI feel like a toy or forces users back to Zitadel console / direct API calls.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Login via Zitadel OIDC** | Authentication is the entry point. Users log in once, same account works in QGIS and web. | LOW | Standard OIDC Authorization Code flow with PKCE. Next.js has established patterns for this. |
| **User list with role display** | Admin needs to see who has access and what they can do. Every admin panel has this. | LOW | Read from Zitadel Management API. Display name, email, role, active/inactive status. |
| **Create user** | Admin must be able to onboard new team members without leaving the app. Going to Zitadel console is unacceptable for non-technical admins. | MEDIUM | Call Zitadel Management API to create human user + assign project role grant. Must handle email invitation flow. |
| **Deactivate/reactivate user** | Users leave, go on leave, or need temporary suspension. Hard delete is dangerous; deactivation is expected. | LOW | Zitadel API supports DeactivateUser/ReactivateUser. UI shows toggle or action button. |
| **Assign/change user role** | Role changes happen (field worker becomes designer, new PM joins). Must be doable from the web. | LOW | Zitadel API: update user grant with new roles. Dropdown with 4 role options. |
| **Project list** | Every user needs to see projects they can access. This is the landing page after login. | LOW | Already have GET /projects endpoint. Add filtering by user assignment. |
| **Create project** | PM/Admin creates new fiber network projects. Core CRUD already exists in API. | LOW | POST /projects already exists. Add UI form: name, description, area (optional). |
| **Edit project** | Project names change, descriptions need updating. Basic expectation. | LOW | PUT /projects/{id} already exists. Inline edit or modal form. |
| **Assign users to project** | A project needs a team. Admin/PM must assign designers and field workers to specific projects. | MEDIUM | Needs new API endpoint + junction table (project_users). This is the core "who works on what" relationship. |
| **View project members** | When looking at a project, you must see who is assigned. | LOW | Read from project_users junction table. Show name, role, assignment date. |
| **Role-based navigation** | Different roles see different things. Admin sees user management; Field Worker does not. | LOW | Conditional UI rendering based on JWT role claims. No new API needed. |
| **Responsive layout** | Field workers and PMs use tablets and phones. The web UI must work on mobile screens. | MEDIUM | Responsive CSS / mobile-first design. Not a native app, but must be usable on mobile Safari/Chrome. |
| **Session management** | User expects to stay logged in, and to be able to log out. Token refresh must work silently. | LOW | OIDC refresh token handling. Logout clears session and redirects to Zitadel logout. |
| **My profile page** | User can see their own name, email, role. Basic self-service. | LOW | GET /auth/me already exists. Display-only page (edits go through Zitadel). |

### Differentiators (Competitive Advantage)

These features elevate the platform from "basic admin panel" to "proper infrastructure management tool." Not required for v1 launch but high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Project dashboard with stats** | At-a-glance view of project health: element counts, sync status, team size, last activity. Saves time vs. opening QGIS to check progress. | MEDIUM | Aggregate queries on existing tables (count of ftth_okna, ftth_stubovi, cables, work orders per project). No new data needed. |
| **Activity feed / audit log** | Shows "who did what when" at project level. Critical for accountability in construction. PM can see sync uploads, work order changes, user assignments. | MEDIUM | Log table already exists (sync_log). Extend with user management actions. Display as chronological feed. |
| **Project status field** | Projects move through lifecycle: Planning -> Design -> Construction -> As-Built -> Completed. Status tracking is standard in construction management (Procore, Sitetracker, IQGeo all have this). | LOW | Add status column to projects table. Dropdown with predefined states. Filterable in list. |
| **Bulk user assignment** | Assign multiple users to a project at once, or assign one user to multiple projects. Saves clicks when onboarding a team. | LOW | UI convenience over single-assignment. Same API, just batched calls. |
| **Project filtering and search** | Filter projects by status, assigned user, date range. Search by name. Essential once you have more than 10 projects. | LOW | Client-side filtering for small datasets. Server-side pagination if > 100 projects. |
| **Remove user from project** | Un-assign users when they move to different projects or leave the team. | LOW | Delete from project_users junction table. Simple API endpoint. |
| **User invitation with role pre-selection** | When creating a user, pre-select their role and project assignment in one flow. Streamlines onboarding. | MEDIUM | Combines Zitadel user creation + role grant + project_users insert into single UI wizard. Multiple API calls behind one form. |
| **Last login / last active indicator** | Admin can see who has been active recently. Identifies inactive accounts for cleanup. | LOW | Read from Zitadel user metadata or session API. Display relative timestamp. |
| **Project area on map preview** | Small static map showing project bounds_geom. Gives spatial context without opening QGIS. | MEDIUM | Use Leaflet or MapLibre for small embedded map. bounds_geom already exists in projects table. |
| **Export project summary** | Export project metadata + team + element counts as PDF or CSV. Useful for reporting to management or clients. | MEDIUM | Server-side PDF generation or client-side CSV. Requires gathering data from multiple tables. |
| **Password reset trigger** | Admin can trigger password reset email for a user who is locked out. Without this, admin must go to Zitadel console. | LOW | Zitadel API supports SetHumanPassword or SendPasswordResetEmail. Single button in user detail view. |

### Anti-Features (Deliberately NOT Building)

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| **Full user profile editing in WebUI** | "Let admins edit user emails and names directly" | Zitadel is the source of truth for identity data. Duplicating profile editing creates sync issues and data conflicts. Users should manage their own profile in Zitadel or via self-service. | Admin can trigger invitation/password reset. Users edit their own profile via Zitadel account page. Display user data read-only in WebUI. |
| **Custom permission matrix per project** | "Different users should have different fine-grained permissions per project" | Massive complexity. RBAC with 4 roles is sufficient for this domain. Per-project permission overrides create confusion and maintenance burden. Procore has this but serves thousands of companies with complex org structures -- FiberQ does not. | Use 4 fixed roles. Project assignment controls access scope. Role controls action scope. Keep it simple. |
| **Real-time collaborative editing** | "Multiple users editing the same project simultaneously with live cursors" | The design work happens in QGIS, not the web. WebUI is for admin/management, not collaborative design. Real-time adds massive WebSocket complexity for zero benefit. | QGIS handles design collaboration via sync. Web shows read-only project state. Edits to metadata are low-frequency and non-conflicting. |
| **Built-in chat / messaging** | "Team communication within the platform" | Chat is a product in itself. Users already have Viber, Telegram, Teams. Building chat diverts from core value and never matches dedicated tools. | Link to external communication channels from project pages if needed. |
| **Notification system with email/push** | "Email alerts when assigned to project, push notifications for status changes" | Premature at this scale (tens of users). Email delivery infrastructure (SMTP, bounce handling, unsubscribe) is a significant side project. Push notifications require service workers. | In-app notification badge at most. Email notifications can be a v2+ feature once core is stable. |
| **Multi-tenancy / organization management** | "Multiple companies using the same deployment" | FiberQ is single-organization. Zitadel handles multi-org at the IdP level if needed. Building multi-tenancy into the app adds complexity to every query and every permission check. | Single-tenant deployment. If needed, deploy separate instances per organization. |
| **Kanban / Gantt project views** | "Visual project management boards" | This is project management tooling (Jira, Asana territory). FiberQ's "projects" are fiber network design scopes, not task-driven project plans. The metaphor doesn't map. | Simple list view with status filters. Work orders (existing feature) cover task-level tracking. |
| **Map-based network visualization in WebUI** | "Show the fiber network on a web map" | Explicitly out of scope for this milestone (stated in PROJECT.md). This is a major undertaking requiring full GIS rendering capability. | Defer to next milestone. QGIS remains the map tool. Small static map preview for project area is the limit for v1. |

---

## Feature Dependencies

```
[Zitadel OIDC Login]
    |
    +---> [User List] ---> [Create User]
    |         |                  |
    |         +---> [Deactivate/Reactivate User]
    |         +---> [Assign/Change Role]
    |         +---> [Password Reset Trigger]
    |         +---> [Last Login Indicator]
    |
    +---> [Project List] ---> [Create Project]
    |         |                    |
    |         +---> [Edit Project]
    |         +---> [Project Status Field]
    |         +---> [Project Filtering/Search]
    |
    +---> [Project-User Assignment] --requires--> [User List] + [Project List]
    |         |
    |         +---> [View Project Members]
    |         +---> [Remove User from Project]
    |         +---> [Bulk User Assignment]
    |
    +---> [My Profile Page]
    |
    +---> [Role-Based Navigation] --requires--> [Zitadel OIDC Login]
    |
    +---> [Responsive Layout] (cross-cutting, no dependency)
    +---> [Session Management] --requires--> [Zitadel OIDC Login]

[Project Dashboard with Stats] --requires--> [Project List] + [Project-User Assignment]
    |
    +--enhances--> [Activity Feed] --requires--> [Audit Log table extension]
    +--enhances--> [Project Area Map Preview] --requires--> [bounds_geom in projects]

[User Invitation Wizard] --requires--> [Create User] + [Assign Role] + [Project-User Assignment]

[Export Project Summary] --requires--> [Project Dashboard with Stats]
```

### Dependency Notes

- **Everything requires Zitadel OIDC Login:** Authentication is the prerequisite for all features. Build this first.
- **Project-User Assignment requires both User List and Project List:** The junction table connects users to projects. Both must exist before assignment makes sense.
- **Activity Feed requires audit log infrastructure:** The sync_log table exists but needs to be extended to cover user management and project management actions.
- **User Invitation Wizard combines multiple atomic features:** It orchestrates user creation + role assignment + project assignment. Build the atoms first, then compose the wizard.
- **Project Dashboard with Stats requires Project-User Assignment:** Counts and summaries are meaningless without knowing who works on what.

---

## MVP Definition

### Launch With (v1)

The minimum to make the WebUI useful for an admin and browsable for team members.

- [x] **Zitadel OIDC Login** -- without this, nothing works
- [x] **User list with role display** -- admin's primary view
- [x] **Create user with role assignment** -- onboarding flow
- [x] **Deactivate/reactivate user** -- user lifecycle management
- [x] **Project list** -- every user's landing page
- [x] **Create/edit project** -- PM/Admin creates projects
- [x] **Assign users to project** -- connects people to work
- [x] **View project members** -- see who is on a team
- [x] **Role-based navigation** -- different views per role
- [x] **My profile page** -- self-service identity check
- [x] **Session management** -- login/logout/refresh
- [x] **Responsive layout** -- must work on tablets at minimum

### Add After Validation (v1.x)

Features to add once core admin flow is working and in use.

- [ ] **Project status field** -- add when projects need lifecycle tracking
- [ ] **Project filtering and search** -- add when project count exceeds ~15
- [ ] **Project dashboard with stats** -- add once there is real data to display
- [ ] **Activity feed / audit log** -- add once accountability becomes a need
- [ ] **Remove user from project** -- add when team reassignment becomes frequent
- [ ] **Bulk user assignment** -- add when onboarding happens in batches
- [ ] **Password reset trigger** -- add when support requests come in
- [ ] **Last login indicator** -- add when account hygiene matters
- [ ] **Assign/change role (standalone)** -- role changes separate from user creation

### Future Consideration (v2+)

Features that require significant additional infrastructure or belong in later milestones.

- [ ] **Project area map preview** -- requires map library integration, aligns with next milestone (web map visualization)
- [ ] **Export project summary** -- requires reporting infrastructure, PDF generation
- [ ] **User invitation wizard** -- UX polish over atomic features, build when onboarding friction is high
- [ ] **Email notifications** -- requires SMTP infrastructure, templates, unsubscribe handling

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Zitadel OIDC Login | HIGH | LOW | P1 |
| User list with roles | HIGH | LOW | P1 |
| Create user + role | HIGH | MEDIUM | P1 |
| Deactivate/reactivate user | HIGH | LOW | P1 |
| Project list | HIGH | LOW | P1 |
| Create/edit project | HIGH | LOW | P1 |
| Assign users to project | HIGH | MEDIUM | P1 |
| View project members | HIGH | LOW | P1 |
| Role-based navigation | HIGH | LOW | P1 |
| My profile page | MEDIUM | LOW | P1 |
| Session management | HIGH | LOW | P1 |
| Responsive layout | HIGH | MEDIUM | P1 |
| Project status field | MEDIUM | LOW | P2 |
| Project filtering/search | MEDIUM | LOW | P2 |
| Project dashboard with stats | MEDIUM | MEDIUM | P2 |
| Activity feed / audit log | MEDIUM | MEDIUM | P2 |
| Remove user from project | MEDIUM | LOW | P2 |
| Bulk user assignment | LOW | LOW | P2 |
| Password reset trigger | MEDIUM | LOW | P2 |
| Last login indicator | LOW | LOW | P2 |
| Project area map preview | MEDIUM | MEDIUM | P3 |
| Export project summary | LOW | MEDIUM | P3 |
| User invitation wizard | LOW | MEDIUM | P3 |
| Email notifications | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (12 features -- forms the WebUI v1)
- P2: Should have, add iteratively (9 features -- extends v1 into v1.x)
- P3: Nice to have, future milestone (4 features -- requires additional infrastructure)

---

## Competitor Feature Analysis

| Feature Area | VETRO FiberMap | IQGeo Network Manager | Procore (construction) | FiberQ WebUI (our approach) |
|--------------|----------------|----------------------|------------------------|-----------------------------|
| User management | Dashboard with API access management, role-based permissions | User and group roles as core features | Granular per-tool permission levels (None/Read/Standard/Admin) | 4 fixed roles via Zitadel, admin creates/deactivates users from WebUI |
| Project management | Phases, tags, archiving, search. Map-based navigation. | Task automation by role and type. Status reporting. | Custom project roles, permission templates, project directory | CRUD + user assignment + status. Simple and focused. |
| Dashboard | Network dashboard with analytics in polygons, visual reporting | Real-time task and project visibility | Project-level dashboards per tool | Project stats (element counts, sync status, team) |
| Field access | Browser-based map viewer | Mobile task reporting, offline support | Mobile app with role-based views | QField handles field work; WebUI is responsive for basic admin on tablets |
| Role system | Role-based map access | Tasks assigned by role and team type | 4 permission levels x per-tool granularity + custom roles | 4 roles (Admin, PM, Designer, Field Worker). Simple hierarchy. |
| Audit / activity | Not prominently featured | Every task logged, timestamped, auditable | Action-level audit logs per project | Sync log exists; extend with user/project management events |

**Key insight from competitor analysis:** Enterprise fiber management tools (VETRO, IQGeo) are primarily GIS/mapping platforms with admin features bolted on. Construction management tools (Procore) have deep permission systems because they serve thousands of organizations. FiberQ is neither -- it is a single-organization tool where QGIS is the design environment and the web is purely administrative. The admin UI should be **simple, opinionated, and focused** rather than flexible and configurable.

---

## Implementation Notes by Feature Group

### User Management (Zitadel Integration)

The WebUI acts as a proxy to the Zitadel Management API for user lifecycle operations. Key considerations:

- **Service account required:** The FastAPI backend needs a Zitadel service account with Management API access to create users, assign roles, and manage lifecycle.
- **User creation flow:** Create user in Zitadel -> assign role (project grant) -> optionally assign to FiberQ project. The Zitadel invitation email handles password setup.
- **Role mapping:** Zitadel roles (admin, project_manager, designer, field_worker) map to UI capabilities. The existing role hierarchy (admin > engineer > field_worker) needs updating to the 4-role model.
- **Read-only identity data:** Names and emails come from Zitadel. The WebUI displays but does not edit them. This avoids data duplication.

### Project Management (Existing API Extension)

The project CRUD already exists. Extensions needed:

- **project_users junction table:** New table linking user subs to project IDs with role and assignment date.
- **Filtered project list:** Users who are not admin should only see projects they are assigned to.
- **Project status:** New column on existing projects table with enum values.
- **Stats aggregation:** COUNT queries on ftth_* tables grouped by project_id.

### Dashboard

The dashboard is not a separate system -- it is computed views over existing data:

- **Per-project stats:** Element counts from ftth_okna, ftth_stubovi, ftth_kablovi_*, work_orders, fiber_splice_closures.
- **Team view:** Users assigned to project from project_users.
- **Recent activity:** From sync_log and new audit_log entries.
- **No new data storage needed** for basic dashboard. All data already exists.

---

## Sources

- [VETRO FiberMap product page](https://vetrofibermap.com/products/fibermap/) -- MEDIUM confidence (marketing material)
- [IQGeo Network Manager Telecom](https://www.iqgeo.com/products/network-manager-telecom) -- MEDIUM confidence (product overview)
- [IQGeo Workflow Manager](https://www.iqgeo.com/products/workflow-manager) -- MEDIUM confidence (feature descriptions)
- [Procore Admin Tool documentation](https://support.procore.com/products/online/user-guide/company-level/admin) -- HIGH confidence (official docs)
- [Procore Custom Project Roles](https://support.procore.com/faq/what-are-custom-project-roles) -- HIGH confidence (official docs)
- [Autodesk Construction Cloud permissions](https://construction.autodesk.com/tools/construction-team-and-user-permissions/) -- HIGH confidence (official docs)
- [Zitadel User Management docs](https://zitadel.com/docs/guides/manage/console/users) -- HIGH confidence (official docs)
- [Zitadel Roles documentation](https://zitadel.com/docs/guides/manage/console/roles) -- HIGH confidence (official docs)
- [Zitadel API introduction](https://zitadel.com/docs/apis/introduction) -- HIGH confidence (official docs)
- [Vitruvi Top 8 Fiber Software](https://vitruvisoftware.com/blog/fiber-network-management-software) -- LOW confidence (vendor comparison blog)
- [ITS-NetProgress / FTTHPlanning.com](https://ftthplanning.com/) -- MEDIUM confidence (product page)
- [Setics FiberState](https://www.setics.com/en/expertise/software/fiberstate/) -- MEDIUM confidence (product page)
- [FTTH/FTTX trends 2024-2030](https://splice.me/blog/trends-in-ftth-fttx-network-design-software-2024-to-2030/) -- LOW confidence (blog)

---
*Feature research for: FTTX/Fiber Optic Network Management WebUI*
*Researched: 2026-02-21*

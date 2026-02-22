---
phase: 03-project-management-assignment
verified: 2026-02-22T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 3: Project Management and Assignment Verification Report

**Phase Goal:** Users can manage projects and assign team members, with visibility scoped by role and assignment
**Verified:** 2026-02-22
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A non-admin user sees only projects they are assigned to; an admin sees all projects | VERIFIED | `routes.py` lines 76-93: `if user.is_admin or "project_manager" in user.roles` fetches all projects; else JOINs on `project_users WHERE pu.user_sub = $1`. Detail endpoint also enforces 403 for non-assigned non-admin/PM users (lines 199-206). |
| 2 | Admin or Project Manager can create a project with name and description, and it appears in the project list | VERIFIED | `routes.py` line 159: `Depends(require_project_manager_or_admin)` guards POST /. Frontend `page.tsx` lines 45-47 computes `canCreate` from admin or project_manager role and passes to `ProjectsClient`, which shows "Create Project" button only when `canCreate`. `createProject` server action calls `POST /projects`. |
| 3 | Admin or Project Manager can assign a user to a project, and that user then sees the project in their list | VERIFIED | `routes.py` lines 327-374: `POST /{project_id}/members` with upsert INSERT INTO project_users. Permission checked via `_check_project_manager_permission` (admin OR global PM OR project-level manager). Frontend `member-combobox.tsx` calls `assignMember` server action on submit; `project-members.tsx` renders combobox only when `canManage`. After assignment, user's `user_sub` is in `project_users`, so the list query JOIN will return the project to them. |
| 4 | User can view the members assigned to a project with their names and roles | VERIFIED | `routes.py` lines 209-216: `GET /{project_id}` fetches members from `project_users` and returns `ProjectDetailOut` with `members: list[ProjectMemberOut]`. Frontend `project-members.tsx` renders each member with initials avatar, `userDisplayName`, `userEmail`, and role Badge using `ROLE_BADGE_VARIANT` mapping (manager=default, specialist=secondary, observer=outline). |
| 5 | User can filter and search projects by name, status, and assigned user | VERIFIED | `routes.py` list endpoint returns `member_names` list per project (batch-fetched from `project_users`). `projects-client.tsx` lines 57-74: three independent client-side filters — `searchQuery` (case-insensitive name match), `statusFilter` (exact status match), `userFilter` (memberNames includes check). All three filter dropdowns/inputs rendered in the filter bar. |

**Score:** 5/5 truths verified

---

## Required Artifacts

### Plan 01: Backend (server/)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `server/db/init.sql` | `project_users` table and `status` column on projects | VERIFIED | Lines 444-463: `ALTER TABLE projects ADD COLUMN IF NOT EXISTS status`, `CREATE TABLE IF NOT EXISTS project_users` with CHECK constraint, UNIQUE, 2 indexes, grants. 5 occurrences of `project_users`. |
| `server/api/projects/models.py` | Pydantic models for project CRUD | VERIFIED | 6 models (ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetailOut, ProjectMemberOut, AssignMemberBody) + 2 constants (PROJECT_STATUSES, PROJECT_ROLES). All contain required fields. Syntax valid. |
| `server/api/projects/routes.py` | Role-scoped list, detail with members/extent, assignment endpoints | VERIFIED | 8 endpoints. Uses `project_users` in all relevant queries. PostGIS UNION ALL extent computation present (ST_Extent, ST_AsGeoJSON). Permission helper `_check_project_manager_permission` covers admin / global PM / project-level manager. Syntax valid. |
| `server/api/auth/roles.py` | `require_project_manager_or_admin` dependency | VERIFIED | Line 23: `require_project_manager_or_admin = require_role("admin", "project_manager")`. Syntax valid. |

### Plan 02: Frontend list page (web/src/)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `web/src/types/project.ts` | ProjectCard, ProjectDetail, ProjectMember, CreateProjectInput, AssignableUser types | VERIFIED | All 5 types exported. Correct camelCase fields. |
| `web/src/app/[locale]/projects/page.tsx` | Server Component fetching from /projects with role check | VERIFIED | Calls `apiFetch<ApiProject[]>("/projects")`, computes `canCreate` from session roles, passes to `ProjectsClient`. |
| `web/src/app/[locale]/projects/_actions.ts` | Server actions for project CRUD and member management | VERIFIED | 5 exported async functions: createProject, updateProject, assignMember, removeMember, fetchAssignableUsers. All follow discriminated union pattern with try/catch and revalidatePath. |
| `web/src/app/[locale]/projects/_components/projects-client.tsx` | Client wrapper with filters, grid, empty states | VERIFIED | Three-filter logic (name/status/user), card grid, role-scoped empty states, create dialog trigger. |
| `web/src/app/[locale]/projects/_components/project-card.tsx` | Card with mini-map, status badge, member count | VERIFIED | Renders project.name, status badge via `getStatusBadgeProps`, memberCount. |
| `web/src/app/[locale]/projects/_components/project-mini-map.tsx` | MapLibre GL lazy-loaded mini-map with optional interactive prop | VERIFIED | IntersectionObserver lazy load, `interactive` prop (default false), NavigationControl added only when `interactive=true`. |
| `web/src/app/[locale]/projects/_components/create-project-dialog.tsx` | Modal dialog with zod validation | VERIFIED | Imports `createProject` from `_actions`, uses react-hook-form + zod, calls action on submit. |

### Plan 03: Frontend detail page (web/src/)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `web/src/app/[locale]/projects/[id]/page.tsx` | Server Component detail page | VERIFIED | Calls `apiFetch<ApiProjectDetail>(\`/projects/${id}\`)`, maps snake_case, computes `canManage` from three sources, two-column layout with ProjectMiniMap (interactive) and ProjectDetailActions. |
| `web/src/app/[locale]/projects/_components/project-detail-actions.tsx` | Client bridge with members card and edit dialog | VERIFIED | Renders `ProjectMembers` and conditionally renders actions card with "Edit Project" button; controls `showEditDialog` state; renders `EditProjectDialog`. |
| `web/src/app/[locale]/projects/_components/project-members.tsx` | Members list with role badges and X remove button | VERIFIED | ScrollArea wrapping member rows, initials avatar, userDisplayName/userEmail display, role Badge, X button opening ConfirmActionDialog on click, calls `removeMember` on confirm. |
| `web/src/app/[locale]/projects/_components/member-combobox.tsx` | Command+Popover combobox for user assignment | VERIFIED | Lazy-loads users via `fetchAssignableUsers` on popover open, filters out existing members, role Select, calls `assignMember` on "Add" button click, toast feedback, router.refresh(). |
| `web/src/app/[locale]/projects/_components/edit-project-dialog.tsx` | Edit dialog with zod validation | VERIFIED | react-hook-form + zod schema (name/description/status), pre-fills form, calls `updateProject` server action on submit, toast feedback, closes on success. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `server/api/projects/routes.py` | `server/db/init.sql` | SQL queries on `project_users` | WIRED | `project_users` appears in 6 distinct SQL queries across list, detail, assign, remove, check-permission, and assignable-users endpoints. |
| `server/api/projects/routes.py` | `server/api/auth/roles.py` | `Depends(require_project_manager_or_admin)` | WIRED | Lines 159 (create_project) and 315 (delete_project). Permission helper also checks `user.is_admin` and `"project_manager" in user.roles` inline. |
| `web/src/app/[locale]/projects/[id]/page.tsx` | `/projects/{id}` API | `apiFetch('/projects/${id}')` | WIRED | Line 88: `apiFetch<ApiProjectDetail>(\`/projects/${id}\`)` with snake_case-to-camelCase mapping. |
| `web/src/app/[locale]/projects/_components/member-combobox.tsx` | `web/src/app/[locale]/projects/_actions.ts` | `assignMember` server action | WIRED | Line 31 import, line 93 call: `assignMember(projectId, { user_sub, user_display_name, user_email, project_role })`. |
| `web/src/app/[locale]/projects/_components/project-members.tsx` | `web/src/app/[locale]/projects/_actions.ts` | `removeMember` server action | WIRED | Line 20 import, line 58 call: `removeMember(projectId, confirmRemove.id)`. |
| `member-combobox.tsx` | `_actions.ts` `fetchAssignableUsers` | `useEffect` on popover open | WIRED | Line 70: `fetchAssignableUsers(projectId)` called in useEffect when `open` is true. Result maps to `AssignableUser[]` and filtered against `existingMemberSubs`. |
| `edit-project-dialog.tsx` | `_actions.ts` `updateProject` | `onSubmit` handler | WIRED | Line 36 import, line 101 call: `updateProject(project.id, { name, description, status })`. |

---

## Requirements Coverage

All five success criteria from the phase are satisfied:

| Success Criterion | Status | Supporting Evidence |
|-------------------|--------|---------------------|
| Non-admin sees only assigned projects; admin sees all | SATISFIED | Role-scoped SQL in `list_projects`, 403 guard in `get_project` |
| Admin/PM can create project with name/description, appears in list | SATISFIED | `POST /` with `require_project_manager_or_admin`, status validation, frontend create dialog |
| Admin/PM can assign user; user then sees project | SATISFIED | `POST /{id}/members` upsert, `_check_project_manager_permission`, combobox UI |
| User can view members with names and roles | SATISFIED | `GET /{id}` returns members list, `project-members.tsx` renders with role badges |
| User can filter/search by name, status, assigned user | SATISFIED | `member_names` returned by list API, three client-side filters in `projects-client.tsx` |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `project-members.tsx` | 106 | `{/* Avatar placeholder */}` comment | Info | This is a descriptive comment on the initials circle implementation, not a stub. The initials are fully implemented. No impact. |
| `member-combobox.tsx` | 133 | `placeholder={t("searchUsers")}` | Info | This is a proper HTML input placeholder attribute, not a stub indicator. |
| `edit-project-dialog.tsx` | 135, 152 | `placeholder={t("namePlaceholder")}` | Info | Proper HTML input placeholder attributes using i18n keys. |

No blockers or warnings found. All three "placeholder" occurrences are legitimate HTML `placeholder` attributes or code comments, not stub implementations.

---

## Human Verification Required

The following behaviors cannot be verified programmatically and require manual testing:

### 1. Role-Scoped Visibility (End-to-End)

**Test:** Log in as a non-admin, non-PM user who is NOT assigned to any project. Navigate to /projects.
**Expected:** Empty state with "No projects assigned to you" message (not the admin empty state).
**Why human:** Cannot run the app against a live Kanidm instance to test actual auth token role claims.

### 2. Member Assignment Flow

**Test:** Log in as admin or project manager. Go to a project detail page. Open the member combobox, search for a user, select a role, click "Add".
**Expected:** User appears in the members list after router.refresh(). Toast "Member assigned successfully" appears.
**Why human:** Requires live database with users in `user_logins` table and a live API.

### 3. Assigned User Sees Project

**Test:** Assign user A to Project X (as admin). Log in as user A. Navigate to /projects.
**Expected:** Project X appears in user A's project list.
**Why human:** Requires two browser sessions with different user identities.

### 4. Interactive Map on Detail Page

**Test:** Navigate to a project detail page for a project with geographic data.
**Expected:** MapLibre map renders with NavigationControl (zoom +/- buttons visible, pan works). Card mini-maps on the list page remain static (no NavigationControl).
**Why human:** WebGL rendering and interactive controls require visual/manual inspection.

### 5. Filter: Assigned User Dropdown

**Test:** On the projects list page, click the "All users" dropdown.
**Expected:** Dropdown shows names of users assigned to visible projects. Selecting a name filters the grid to only projects that user is assigned to.
**Why human:** Requires live data with actual member_names populated from the backend.

---

## Gaps Summary

No gaps found. All five observable truths are fully verified:

- The backend is complete and substantive: 8 API endpoints with real SQL queries, role-scoped visibility, upsert assignment, PostGIS extent computation, HTTP 400 for invalid roles, and permission helper correctly combines admin / global PM / project-level manager.
- The frontend is complete and wired: detail page fetches from API, maps snake_case to camelCase, passes canManage to client components, member combobox lazily fetches assignable users and calls assignMember, ConfirmActionDialog reused from Phase 2, edit dialog calls updateProject, three-filter client-side logic using memberNames returned from API.
- All 6 git commits exist and are valid.
- Python syntax valid for all three backend files.
- No stubs, empty returns, or unimplemented handlers found.

---

*Verified: 2026-02-22*
*Verifier: Claude (gsd-verifier)*

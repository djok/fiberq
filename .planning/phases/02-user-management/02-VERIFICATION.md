---
phase: 02-user-management
verified: 2026-02-21T22:00:00Z
status: passed
score: 14/14 must-haves verified
re_verification: false
---

# Phase 2: User Management Verification Report

**Phase Goal:** Admins can manage the full user lifecycle from the WebUI without touching the Kanidm console
**Verified:** 2026-02-21T22:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | GET /api/users returns a list of all Kanidm persons with name, email, roles, active status, and last login | VERIFIED | `routes.py` L77-106: `@router.get("")` queries `kanidm.list_persons()`, fetches `user_logins`, parses each person through `_parse_person()` returning `UserListOut` |
| 2  | POST /api/users creates a person in Kanidm, assigns groups, and returns a credential reset token | VERIFIED | `routes.py` L132-161: creates person, sets mail/phone attrs, loops roles to add group members, calls `create_credential_reset_token`, returns `CredentialResetOut` |
| 3  | POST /api/users/{id}/deactivate sets account_expire to epoch, POST /api/users/{id}/reactivate clears it | VERIFIED | `routes.py` L164-187: deactivate calls `kanidm.deactivate_person()` which calls `set_person_attr(id, "account_expire", ["1970-01-01T00:00:00+00:00"])`; reactivate calls `delete_person_attr(id, "account_expire")` |
| 4  | PUT /api/users/{id}/roles replaces group memberships for the fiberq_* groups | VERIFIED | `routes.py` L190-212: loops all `FIBERQ_ROLE_GROUPS`, adds/removes each group membership based on `body.roles` |
| 5  | POST /api/users/{id}/reset-password returns a credential reset token | VERIFIED | `routes.py` L215-229: calls `create_credential_reset_token(user_id, 3600)`, returns `CredentialResetOut` |
| 6  | Each WebUI login records last_login_at in the user_logins table | VERIFIED | `auth/routes.py` L28-42: `POST /auth/record-login` upserts `(user_sub, username, NOW(), 'web')` into `user_logins`; `web/src/auth.ts` L80-85: fire-and-forget fetch to `/auth/record-login` in `if (account)` jwt callback block |
| 7  | Admin can view a paginated data table of all users with Name, Email, Role badges, Status badge, Last Login, and Actions columns | VERIFIED | `columns.tsx`: 6 column definitions (displayName, email, roles as Badge array, isActive as Badge, lastLogin formatted, actions); `data-table.tsx`: TanStack table with pagination controls, 20 rows default |
| 8  | Text search filters table rows by name or email | VERIFIED | `data-table.tsx` L61-71: `globalFilterFn` checks `displayName`, `email`, `username`; `data-table-toolbar.tsx` L32-34: Input sets `table.setGlobalFilter` |
| 9  | Dropdown filters allow filtering by role and by active/inactive status | VERIFIED | `data-table-toolbar.tsx` L38-77: two Select components filter `roles` column and `isActive` column; `columns.tsx` L89-92, L103-108: custom `filterFn` implementations for both |
| 10 | Deactivated users show dimmed row with red Inactive badge | VERIFIED | `data-table.tsx` L114-115: `opacity-60 bg-muted/30` class on inactive rows; `columns.tsx` L97-102: `Badge variant="destructive"` for inactive status |
| 11 | Admin can open a Create User modal dialog from a button above the table | VERIFIED | `users-client.tsx`: `<CreateUserDialog />` passed as `createButton` prop to `DataTable`; `data-table.tsx` L89: toolbar rendered with createButton; `data-table-toolbar.tsx` L79: `ml-auto` create button placement |
| 12 | Create User form has fields: Username, Display Name, Email, Phone (optional), Role(s) with multi-select | VERIFIED | `create-user-dialog.tsx` L181-277: FormField for username, displayName, email, phone (type="tel"), and roles as 4 Checkbox components with multi-select logic |
| 13 | After creating a user, a credential reset token is displayed for the admin to share | VERIFIED | `create-user-dialog.tsx` L120-169: on success, `resetData` state set, dialog switches to token display view with monospace code block, copy button, reset URL link |
| 14 | Admin can click a table row to navigate to /users/[id] detail page, with profile data, roles, status, actions, and projects placeholder section | VERIFIED | `data-table.tsx` L117-119: `onClick` navigates to `/${locale}/users/${row.original.id}`; `[id]/page.tsx`: profile card, status badge; `user-detail-actions.tsx`: Roles card with Edit button, Actions card (deactivate/reactivate, reset password), Projects placeholder card, Account Info card |

**Score: 14/14 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `server/api/users/kanidm_client.py` | Kanidm REST API client using service account token (min 80 lines) | VERIFIED | 171 lines, `KanidmAdminClient` class with 12 async methods, all Kanidm V1 person + group operations |
| `server/api/users/routes.py` | FastAPI /users router with all CRUD endpoints, exports `router` | VERIFIED | Exports `router = APIRouter()`, 7 `@router.*` endpoints |
| `server/api/users/models.py` | Pydantic models for user CRUD, contains `class UserCreate` | VERIFIED | Contains `UserCreate`, `UserRoleUpdate`, `UserOut`, `UserListOut`, `CredentialResetOut` |
| `server/db/init.sql` | user_logins table for last login tracking, contains `CREATE TABLE user_logins` | VERIFIED | `CREATE TABLE IF NOT EXISTS user_logins` at L431, with index on `last_login_at` |
| `web/src/app/[locale]/users/page.tsx` | Server component that fetches users and renders data table (min 20 lines) | VERIFIED | 65 lines, calls `apiFetch<ApiResponse>("/users")`, maps to `UserRow[]`, renders `<UsersClient>` |
| `web/src/app/[locale]/users/_components/data-table.tsx` | Client component wrapping TanStack React Table (min 40 lines) | VERIFIED | 191 lines, `useReactTable` with sorting/filtering/pagination, proper shadcn Table render |
| `web/src/app/[locale]/users/_components/columns.tsx` | Column definitions for user data table, contains `ColumnDef` | VERIFIED | Contains `ColumnDef<UserRow>[]`, 6 column definitions, `UserActions` wired in actions column |
| `web/src/app/[locale]/users/_components/create-user-dialog.tsx` | Modal dialog form for creating new users, contains `CreateUserDialog` | VERIFIED | `export function CreateUserDialog()`, full form with zod validation and token display success view |
| `web/src/app/[locale]/users/_actions.ts` | Server Actions for user CRUD operations, contains `"use server"` | VERIFIED | `"use server"` directive, 5 exported async functions calling `apiFetch` |
| `web/src/types/user.ts` | TypeScript types for user data, contains `UserRow` | VERIFIED | `export type UserRow`, plus `UserListResponse`, `CreateUserInput`, `CredentialResetResponse`, `UserRoleUpdateInput` |
| `web/src/app/[locale]/users/[id]/page.tsx` | User detail page (min 50 lines) | VERIFIED | 133 lines, Server Component, fetches single user, renders profile card and `<UserDetailActions>` |
| `web/src/app/[locale]/users/_components/user-actions.tsx` | Dropdown menu with quick actions for table rows, contains `UserActions` | VERIFIED | `export function UserActions`, DropdownMenu with View Details/Deactivate/Reactivate/Reset Password items |
| `web/src/app/[locale]/users/_components/confirm-action-dialog.tsx` | Reusable confirmation dialog, contains `ConfirmActionDialog` | VERIFIED | `export function ConfirmActionDialog`, AlertDialog wrapper with loading state |
| `web/src/app/[locale]/users/_components/edit-roles-dialog.tsx` | Dialog for editing user role assignments, contains `EditRolesDialog` | VERIFIED | `export function EditRolesDialog`, react-hook-form + zod, 4 Checkbox inputs, calls `updateUserRoles` |
| `web/src/app/[locale]/users/_components/reset-token-dialog.tsx` | Dialog showing credential reset token with copy button, contains `ResetTokenDialog` | VERIFIED | `export function ResetTokenDialog`, monospace token display, copy button, reset URL link |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `server/api/users/routes.py` | `server/api/users/kanidm_client.py` | `KanidmAdminClient instance` | WIRED | `_get_kanidm_client()` factory at L33-35; all endpoints call `kanidm = _get_kanidm_client()` then `kanidm.*` methods |
| `server/api/users/routes.py` | `server/api/auth/roles.py` | `require_admin dependency` | WIRED | `from auth.roles import require_admin` at L8; all 7 endpoints use `Depends(require_admin)` |
| `server/api/main.py` | `server/api/users/routes.py` | `include_router` | WIRED | L68: `from users.routes import router as users_router`; L71: `app.include_router(users_router, prefix="/users", tags=["users"])` |
| `server/api/auth/routes.py` | `server/db/init.sql` | `INSERT INTO user_logins on login` | WIRED | `auth/routes.py` L32-40: `pool.execute(INSERT INTO user_logins ...)` upsert; `user_logins` table defined in `init.sql` |
| `web/src/auth.ts` | `server/api/auth/routes.py` | `fetch to POST /auth/record-login in jwt callback` | WIRED | `auth.ts` L82-85: `fetch(\`${apiUrl}/auth/record-login\`, { method: "POST", headers: { Authorization: \`Bearer ${account.access_token}\` } }).catch(() => {})` |
| `web/src/app/[locale]/users/page.tsx` | `web/src/lib/api.ts` | `apiFetch to load users` | WIRED | L4: `import { apiFetch } from "@/lib/api"`; L53: `apiFetch<ApiResponse>("/users")` |
| `web/src/app/[locale]/users/_actions.ts` | `web/src/lib/api.ts` | `apiFetch for mutations` | WIRED | L3: `import { apiFetch } from "@/lib/api"`; all 5 actions call `apiFetch` with appropriate paths and methods |
| `web/src/app/[locale]/users/_components/data-table.tsx` | `web/src/app/[locale]/users/_components/columns.tsx` | `columns prop` | WIRED | `users-client.tsx` calls `getColumns()` and passes result as `columns` prop to `DataTable`; `DataTable` uses `columns` in `useReactTable` at L54 |
| `web/src/app/[locale]/users/_components/create-user-dialog.tsx` | `web/src/app/[locale]/users/_actions.ts` | `createUser server action` | WIRED | L31: `import { createUser } from "../_actions"`; `onSubmit` L70: `await createUser({...})` |
| `web/src/app/[locale]/users/_components/user-actions.tsx` | `web/src/app/[locale]/users/_actions.ts` | `server action calls` | WIRED | L20-23: imports `deactivateUser`, `reactivateUser`, `resetUserPassword`; all called in `handleConfirm()` |
| `web/src/app/[locale]/users/[id]/page.tsx` | `web/src/lib/api.ts` | `apiFetch to load single user` | WIRED | L7: `import { apiFetch } from "@/lib/api"`; L59: `apiFetch<ApiUser>(\`/users/${id}\`)` |
| `web/src/app/[locale]/users/_components/edit-roles-dialog.tsx` | `web/src/app/[locale]/users/_actions.ts` | `updateUserRoles server action` | WIRED | L27: `import { updateUserRoles } from "../_actions"`; `onSubmit` L71: `await updateUserRoles(userId, { roles: values.roles })` |

---

### Requirements Coverage

All requirements from Plans 01-03 satisfied:

| Requirement | Status | Notes |
|-------------|--------|-------|
| FastAPI /users/* endpoints (list, get, create, deactivate, reactivate, update-roles, reset-password) | SATISFIED | 7 endpoints confirmed by `@router.*` count |
| All endpoints admin-only | SATISFIED | Every endpoint uses `Depends(require_admin)` |
| KanidmAdminClient with all Kanidm REST operations | SATISFIED | 12 async methods covering person CRUD + group management |
| user_logins table with last login tracking | SATISFIED | Table in `init.sql`, upsert in `auth/routes.py` |
| POST /auth/record-login endpoint | SATISFIED | Present in `auth/routes.py` with upsert logic |
| auth.ts fire-and-forget record-login on sign-in | SATISFIED | Non-blocking fetch in `if (account)` block with `.catch(() => {})` |
| User list page with 6 columns | SATISFIED | `columns.tsx`: displayName, email, roles, isActive, lastLogin, actions |
| Text search + role/status filters | SATISFIED | `data-table-toolbar.tsx` + `globalFilterFn` + column filterFn |
| Pagination (default 20, 10/20/50 selector) | SATISFIED | `initialState.pagination.pageSize = 20`, Select with 10/20/50 |
| Create User dialog with credential token display | SATISFIED | Full form + success view with token/URL/copy button |
| User detail page at /users/[id] | SATISFIED | Server Component at correct route, profile card, status badge |
| Deactivate/Reactivate with confirmation dialogs | SATISFIED | `ConfirmActionDialog` used in both `UserActions` and `UserDetailActions` |
| Edit Roles dialog with checkboxes | SATISFIED | `EditRolesDialog` with 4 Checkbox inputs, zod min-1 validation |
| Password reset with token display | SATISFIED | `ResetTokenDialog` with copy button, used from both table and detail page |
| Projects placeholder section | SATISFIED | Projects placeholder card in `user-detail-actions.tsx` |
| Full bilingual translations (EN + BG) | SATISFIED | 63 keys in `en.json` users namespace, Bulgarian equivalents in `bg.json` |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `data-table-toolbar.tsx` | 32, 47, 70 | `placeholder=` attribute on SelectValue/Input | INFO | These are correct HTML placeholder attributes on form controls, not implementation stubs |

No blockers or warnings found. The "placeholder" strings found are HTML form control placeholder attributes — legitimate usage, not implementation stubs.

---

### Human Verification Required

The following items cannot be verified programmatically:

#### 1. Full sign-in → record-login flow

**Test:** Sign in through the Kanidm OIDC flow, then check the user_logins table
**Expected:** A row exists for the signed-in user with `last_login_at` updated to the current timestamp
**Why human:** Requires a live Kanidm OIDC server and PostgreSQL database; cannot simulate OIDC flow statically

#### 2. Create User → Kanidm credential reset token

**Test:** Click "New User", fill in the form, submit; observe the success view
**Expected:** Credential reset token appears in monospace display with working copy button; token is valid in Kanidm's /ui/reset
**Why human:** Requires live Kanidm service account token (`KANIDM_API_TOKEN`) and network access to Kanidm

#### 3. Deactivate/Reactivate user lifecycle

**Test:** Deactivate a user from the table actions dropdown; observe dimmed row and red Inactive badge after revalidation; reactivate and observe return to active
**Expected:** Confirmation dialog appears, action executes, table refreshes via `revalidatePath`, row styling updates
**Why human:** Requires live backend + browser interaction to observe real-time table updates after server action

#### 4. Role filter accuracy

**Test:** Create users with different roles; use the Role dropdown filter to filter by each role
**Expected:** Only users with that role remain visible
**Why human:** Requires multiple test users in Kanidm; column filterFn logic correct statically but needs data validation

---

### Gaps Summary

No gaps found. All 14 observable truths verified, all 15 artifacts exist and are substantive, all 12 key links are wired.

The implementation is complete and matches the plan specifications with one auto-fixed deviation (UsersClient wrapper component for DataTable/Toolbar coupling) and one additional file created (user-detail-actions.tsx extracted as separate client component file) — both changes were improvements over the plan, not regressions.

**Key implementation notes:**
- `kanidm_verify_tls` field was already present in `config.py` from Phase 1; `kanidm_api_token` added as planned
- `users-client.tsx` was added beyond the plan spec to bridge server/client component boundary cleanly — this is a proper architectural addition
- `user-detail-actions.tsx` holds all 4 right-column cards (Roles, Actions, Projects, Account Info) as a single client component boundary — clean pattern

---

_Verified: 2026-02-21T22:00:00Z_
_Verifier: Claude (gsd-verifier)_

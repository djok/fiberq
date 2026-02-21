---
phase: 02-user-management
plan: 02
subsystem: ui
tags: [tanstack-react-table, react-hook-form, zod, sonner, shadcn-ui, next-intl, server-actions]

# Dependency graph
requires:
  - phase: 02-user-management
    plan: 01
    provides: "FastAPI /users router with 7 CRUD endpoints, Pydantic models, Kanidm admin proxy"
  - phase: 01-auth-app-shell
    provides: "App shell with sidebar, auth.ts, apiFetch utility, bilingual i18n setup"
provides:
  - "User list data table with TanStack React Table (sortable columns, global search, role/status filters, pagination)"
  - "Create User dialog with react-hook-form + zod validation and credential reset token display"
  - "Server Actions for all user CRUD operations (create, deactivate, reactivate, update-roles, reset-password)"
  - "UserRow and related TypeScript types for frontend user data"
  - "Sonner toast provider in root layout"
  - "Full bilingual translations (EN + BG) for user management UI"
affects: [02-user-management, 03-project-management]

# Tech tracking
tech-stack:
  added: ["@tanstack/react-table", "sonner", "zod", "react-hook-form", "@hookform/resolvers"]
  patterns: [server component data fetch + client table wrapper, server actions with discriminated union results, snake_case API to camelCase frontend mapping]

key-files:
  created:
    - web/src/types/user.ts
    - web/src/app/[locale]/users/_actions.ts
    - web/src/app/[locale]/users/_components/columns.tsx
    - web/src/app/[locale]/users/_components/data-table.tsx
    - web/src/app/[locale]/users/_components/data-table-toolbar.tsx
    - web/src/app/[locale]/users/_components/create-user-dialog.tsx
    - web/src/app/[locale]/users/_components/users-client.tsx
  modified:
    - web/src/app/[locale]/users/page.tsx
    - web/src/app/layout.tsx
    - web/src/lib/api.ts
    - web/src/messages/en.json
    - web/src/messages/bg.json
    - web/package.json

key-decisions:
  - "Server component fetches users + maps snake_case to camelCase, passes to client wrapper for table rendering"
  - "DataTable creates table instance internally and renders toolbar with table ref -- avoids lifting state"
  - "Server Actions return discriminated union { success: true, data: T } | { success: false, error: string }"
  - "Graceful fallback: empty table shown when API unavailable (try/catch around apiFetch in page)"

patterns-established:
  - "Data table pattern: server component (fetch) -> UsersClient (columns + translations) -> DataTable (table state) -> DataTableToolbar (filters)"
  - "Create entity dialog pattern: form state -> server action -> success view with result data -> close resets"
  - "snake_case API mapping: explicit mapUser function in server component for backend-to-frontend field translation"

# Metrics
duration: 6min
completed: 2026-02-21
---

# Phase 2 Plan 02: User List Page & Create User Dialog Summary

**TanStack React Table user list with sortable columns, global search, role/status filters, pagination, and Create User dialog with Kanidm credential reset token display**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-21T21:07:48Z
- **Completed:** 2026-02-21T21:14:17Z
- **Tasks:** 2
- **Files modified:** 22

## Accomplishments
- Data-dense user table with 6 columns (Name, Email, Role badges, Status badge, Last Login, Actions) matching CONTEXT.md decisions
- Global text search by name/email/username, role dropdown filter, status dropdown filter
- Paginated table with 20 rows/page default, 10/20/50 page size selector
- Inactive users: dimmed row (opacity-60 + bg-muted/30) with red "Inactive" badge
- Create User modal with Username, Display Name, Email, Phone, Role checkboxes (multi-select)
- Post-creation credential reset token display with copy button and reset URL
- 5 Server Actions for full user CRUD via apiFetch to FastAPI backend
- Full bilingual translations (56 keys each in EN + BG)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies, shadcn/ui components, types, and Sonner provider** - `e55e7c1` (feat)
2. **Task 2: User list page with data table, search/filters, create dialog, and server actions** - `bdc1aec` (feat)

## Files Created/Modified
- `web/src/types/user.ts` - UserRow, CreateUserInput, CredentialResetResponse, UserRoleUpdateInput types
- `web/src/app/[locale]/users/_actions.ts` - 5 Server Actions for user CRUD operations
- `web/src/app/[locale]/users/_components/columns.tsx` - TanStack column definitions with sortable headers, role/status badges, date formatting
- `web/src/app/[locale]/users/_components/data-table.tsx` - Reusable data table with sorting, filtering, pagination, row click navigation
- `web/src/app/[locale]/users/_components/data-table-toolbar.tsx` - Search input, role filter, status filter dropdowns
- `web/src/app/[locale]/users/_components/create-user-dialog.tsx` - Modal form with zod validation, role checkboxes, reset token display
- `web/src/app/[locale]/users/_components/users-client.tsx` - Client wrapper connecting translations, columns, and data to DataTable
- `web/src/app/[locale]/users/page.tsx` - Replaced placeholder with server component fetching users from API
- `web/src/app/layout.tsx` - Added Sonner Toaster component
- `web/src/lib/api.ts` - Handle 204 No Content and error body extraction
- `web/src/messages/en.json` - Added 56 user management translation keys
- `web/src/messages/bg.json` - Added 56 user management translation keys (Bulgarian)
- `web/package.json` - Added @tanstack/react-table, sonner, zod, react-hook-form, @hookform/resolvers
- 8 shadcn/ui components: table, dialog, alert-dialog, form, label, select, sonner, checkbox

## Decisions Made
- Server component fetches users and maps snake_case API response to camelCase UserRow for frontend consistency
- DataTable owns the table instance internally, rendering the toolbar within itself to avoid state-lifting complexity
- Server Actions use discriminated union return type for type-safe error handling in client components
- Graceful degradation: empty table on API error rather than error page (admin can still use the create dialog)
- Added UsersClient wrapper component to bridge server-side data with client-side TanStack table

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added UsersClient wrapper component**
- **Found during:** Task 2 (architecture integration)
- **Issue:** Plan specified toolbar as a ReactNode prop to DataTable, but DataTableToolbar needs the table instance (created inside DataTable). Passing `null as never` for table would break at runtime.
- **Fix:** Created UsersClient wrapper that renders DataTable with createButton prop. DataTable creates table internally and passes it to DataTableToolbar.
- **Files modified:** web/src/app/[locale]/users/_components/users-client.tsx, data-table.tsx
- **Verification:** TypeScript passes, build succeeds
- **Committed in:** bdc1aec (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking architecture issue)
**Impact on plan:** Necessary restructuring for DataTable/Toolbar table instance coupling. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - all components are frontend-only. Backend API endpoints from Plan 01 are already available.

## Next Phase Readiness
- User list page and create flow complete, ready for Plan 03 (user detail page and action dialogs)
- Actions column placeholder ready to be wired to real dropdown menu in Plan 03
- Server Actions for deactivate, reactivate, updateRoles, resetPassword ready for use
- All translation keys for action confirmations pre-loaded

## Self-Check: PASSED

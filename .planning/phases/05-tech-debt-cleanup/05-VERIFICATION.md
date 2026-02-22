---
phase: 05-tech-debt-cleanup
verified: 2026-02-22T00:45:00Z
status: passed
score: 5/5 must-haves verified
gaps: []
human_verification:
  - test: "Delete project flow end-to-end"
    expected: "Delete button appears for admin/PM, confirmation dialog shows project name, confirming calls DELETE /projects/{id}, redirects to /projects list with success toast"
    why_human: "Client-side router.push redirect and toast notifications require browser to verify"
  - test: "Assignable users includes non-logged-in accounts"
    expected: "Persons created in Kanidm admin UI appear in the member assignment dropdown even before they have ever logged in"
    why_human: "Requires a live Kanidm instance with test users to confirm the Kanidm list_persons call returns non-logged-in persons"
---

# Phase 5: Tech Debt Cleanup Verification Report

**Phase Goal:** Close all tech debt items identified in the v1 milestone audit — fix middleware loading, clean dead code, improve assignable users, add missing UI and auth patterns
**Verified:** 2026-02-22T00:45:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Next.js middleware executes at Edge level (middleware.ts at src/ root, not proxy.ts) | VERIFIED | `web/src/middleware.ts` exists with `export default auth(...)` + `export const config`. `web/src/proxy.ts` is absent. |
| 2 | Assignable users list includes all Kanidm persons, not just those who have logged in | VERIFIED | `list_assignable_users` calls `kanidm.list_persons()` — no `user_logins` query in function body. Returns `{user_sub, display_name, email}` from Kanidm `spn`/`displayname`/`mail` attrs. |
| 3 | `server/api/dependencies.py` no longer exists (dead code removed) | VERIFIED | File absent from filesystem. No import references exist in codebase. |
| 4 | `dashboard/page.tsx` has an explicit `auth()` check matching per-page pattern | VERIFIED | Lines 2, 20-23: `import { auth } from "@/auth"` + `const session = await auth(); if (!session) { redirect(...) }` |
| 5 | Admin/PM can delete a project from the project detail page with confirmation dialog | VERIFIED | `deleteProject` server action exists in `_actions.ts` (DELETE method). `project-detail-actions.tsx` has destructive Button + `ConfirmActionDialog` wired with `deleteProject` import. EN/BG i18n keys present. |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/middleware.ts` | Edge-level auth + i18n middleware | VERIFIED | Contains `export default auth(...)` wrapping async function, `export const config` matcher. 44 lines, substantive implementation. |
| `web/src/proxy.ts` | Should NOT exist | VERIFIED | File is absent from filesystem. |
| `server/api/dependencies.py` | Should NOT exist | VERIFIED | File is absent from filesystem. |
| `web/src/app/[locale]/dashboard/page.tsx` | Dashboard page with auth guard | VERIFIED | `await auth()` on line 20, `redirect()` on line 22, imports from `@/auth` on line 2. |
| `server/api/projects/routes.py` | Kanidm-backed assignable users endpoint | VERIFIED | Lines 633-673: `kanidm.list_persons()` called, `user_logins` absent from function, response shape `{user_sub, display_name, email}` preserved. |
| `web/src/app/[locale]/projects/_actions.ts` | `deleteProject` server action | VERIFIED | Lines 95-110: `export async function deleteProject(projectId)` calls `apiFetch` with `method: "DELETE"` and `revalidatePath`. |
| `web/src/app/[locale]/projects/_components/project-detail-actions.tsx` | Delete button with confirmation dialog | VERIFIED | Lines 15-18: imports `ConfirmActionDialog` and `deleteProject`. Lines 35-36: state. Lines 38-52: handler with router.push redirect. Lines 77-83: destructive Button. Lines 96-105: `ConfirmActionDialog` with all required props. |
| `web/src/messages/en.json` | Delete i18n keys in projects section | VERIFIED | Lines 150-154: `deleteProject`, `confirmDeleteTitle`, `confirmDeleteDescription`, `deleteSuccess`, `deleteError` all present. |
| `web/src/messages/bg.json` | Bulgarian delete i18n keys | VERIFIED | Lines 150-154: All 5 delete keys present with Bulgarian translations. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `web/src/middleware.ts` | Next.js Edge runtime | Convention-based filename at `src/middleware.ts` | WIRED | File is at correct path (`web/src/middleware.ts`), has `export default` + `export const config` — Next.js will load it automatically. |
| `web/src/app/[locale]/dashboard/page.tsx` | `@/auth` | `import { auth } from "@/auth"` | WIRED | Import on line 2, `await auth()` on line 20, redirect on lines 21-23. |
| `server/api/projects/routes.py` | `KanidmAdminClient.list_persons()` | `kanidm_client` import + `_get_kanidm_client()` factory | WIRED | `from users.kanidm_client import KanidmAdminClient` on line 12, `_get_kanidm_client()` factory on lines 32-34, `await kanidm.list_persons()` on line 647. |
| `web/src/app/[locale]/projects/_components/project-detail-actions.tsx` | `web/src/app/[locale]/projects/_actions.ts` | `import { deleteProject } from "../_actions"` | WIRED | Line 18: `import { deleteProject } from "../_actions"`. Used in `handleDeleteProject()` on line 41. |
| `web/src/app/[locale]/projects/_actions.ts` | `DELETE /projects/{id}` | `apiFetch` with `method: "DELETE"` | WIRED | Lines 99-101: `apiFetch(\`/projects/${projectId}\`, { method: "DELETE" })`. |

---

## Requirements Coverage

All 5 success criteria from ROADMAP.md satisfied:

| Requirement | Status | Notes |
|-------------|--------|-------|
| Next.js middleware executes at Edge level (proxy.ts renamed to middleware.ts) | SATISFIED | File renamed, correct convention-based path, exports verified. |
| Assignable users list includes all Kanidm persons, not just those who have logged in | SATISFIED | Endpoint rewritten to use `KanidmAdminClient.list_persons()`. |
| `server/api/dependencies.py` is deleted (dead code removed) | SATISFIED | File absent from filesystem and git history confirms deletion via `git rm`. |
| `dashboard/page.tsx` has an explicit `auth()` check matching per-page pattern | SATISFIED | Auth guard on lines 20-23 matching the pattern in projects/users/profile pages. |
| Admin/PM can delete a project from the project detail page with confirmation dialog | SATISFIED | Full delete flow implemented: button, dialog, server action, backend route, i18n. |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web/src/auth.config.ts` | 5 | Stale comment: "Used by proxy.ts for lightweight auth checks." | Info | Comment refers to old filename (proxy.ts). No functional impact — the file is still loaded by `auth.ts`, just the referencing comment is outdated. |

No blockers or warnings found.

---

## Human Verification Required

### 1. Delete Project Flow End-to-End

**Test:** Log in as admin or PM, navigate to a project detail page, click "Delete Project", observe confirmation dialog shows the project name, click confirm.
**Expected:** Success toast "Project deleted successfully" appears, browser navigates to `/[locale]/projects` list, deleted project is no longer listed.
**Why human:** Client-side `router.push` redirect and Sonner toast notifications require a browser session to verify. The dialog open/close state transitions also cannot be checked programmatically.

### 2. Assignable Users Includes Non-Logged-In Kanidm Persons

**Test:** Create a new person in Kanidm admin UI without letting them log in. Navigate to a project's member assignment flow and open the assignable users dropdown.
**Expected:** The newly created Kanidm person appears in the list even though they have never authenticated.
**Why human:** Requires a live Kanidm instance. The code change is verified (Kanidm `list_persons()` replaces `user_logins` query) but the behavioral outcome needs a real Kanidm environment to confirm.

---

## Gaps Summary

No gaps. All 5 phase goal success criteria are fully implemented and wired:

- **middleware.ts:** Correctly named, substantive implementation, both required exports present (`export default auth(...)` + `export const config`). `proxy.ts` is gone with no orphaned imports.
- **dependencies.py:** Deleted. No references remain in Python source.
- **dashboard/page.tsx:** Auth guard matches established pattern (same as projects, users, profile pages). TypeScript compiles clean.
- **Assignable users (routes.py):** Kanidm `list_persons()` replaces `user_logins` query. Response shape (`user_sub`, `display_name`, `email`) preserved for frontend compatibility. Service accounts and anonymous entries filtered.
- **Delete project UI:** Complete flow — destructive button gated by `canManage`, confirmation dialog with project name interpolation, `deleteProject` server action calling `DELETE /projects/{id}`, redirect to projects list, EN+BG i18n, backend route protected by `require_project_manager_or_admin`.

The one stale comment in `auth.config.ts` (references old `proxy.ts` name) is informational only and has no functional impact.

---

_Verified: 2026-02-22T00:45:00Z_
_Verifier: Claude (gsd-verifier)_

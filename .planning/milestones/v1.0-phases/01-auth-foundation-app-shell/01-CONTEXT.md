# Phase 1: Auth Foundation & App Shell - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a working Next.js application integrated with Zitadel OIDC that supports login, logout, session management, a role-based navigation shell, a profile page, and a responsive layout. This is the foundation all subsequent features render within. No user management CRUD, no project CRUD, no dashboard — just the authenticated shell.

Requirements: AUTH-01, AUTH-02, AUTH-03, AUTH-04, UIUX-01, UIUX-02

</domain>

<decisions>
## Implementation Decisions

### Login flow
- Direct redirect to Zitadel login — no intermediate FiberQ landing page
- Auth errors (wrong password, deactivated account) handled entirely by Zitadel's login UI
- After successful login: role-based redirect — Admin goes to User Management (placeholder), others go to Projects (placeholder)
- Session expiry: silent token refresh without user interruption (refresh token via `offline_access` scope)

### App shell layout
- Collapsible sidebar navigation — full labels on desktop, collapses to icons on tablet/narrow viewport
- Admin sees: Dashboard, Projects, Users, Profile, Logout (full set)
- Non-admin roles see subset: items hidden based on role (e.g., Field Worker sees no Users link)
- FiberQ logo + name displayed in sidebar header
- Mobile/tablet navigation: Claude's discretion (hamburger menu or collapsible sidebar behavior — choose what works best with shadcn/ui sidebar component)

### Profile page
- Shows: name, email, role, assigned projects list, last login timestamp
- Avatar: use Zitadel avatar if available (from userinfo endpoint), fallback to generated initials avatar
- All data is read-only with a "Edit profile" link that opens Zitadel account page in new tab
- Assigned projects list is a placeholder in Phase 1 (data available after Phase 3 project_users table)

### Visual identity
- Color scheme: green/teal — telecom/infrastructure feel
- Theme: follows system preference (prefers-color-scheme), automatic light/dark switching
- Interface style: data-dense, compact — more information per screen (like Jira, Grafana); not sparse/minimal
- Language: bilingual (Bulgarian + English) with language switcher — both languages supported from the start

### Claude's Discretion
- Exact green/teal color palette values (primary, secondary, accent)
- Mobile navigation pattern (hamburger menu vs collapsible sidebar — whichever integrates better with shadcn/ui)
- Loading skeleton design and error state layouts
- Typography choices within "data-dense" constraint
- Exact spacing, padding, border-radius values
- i18n implementation approach (next-intl, custom, etc.)

</decisions>

<specifics>
## Specific Ideas

- Data-dense UI like Jira/Grafana — compact tables, tight spacing, more data visible at once
- Green/teal color scheme evokes telecom/infrastructure industry
- Bilingual from day one — avoid retrofitting i18n later
- Zitadel handles all auth UI (login form, error messages, password recovery) — FiberQ never renders auth forms

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-auth-foundation-app-shell*
*Context gathered: 2026-02-21*

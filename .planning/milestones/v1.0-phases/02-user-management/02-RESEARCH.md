# Phase 2: User Management - Research

**Researched:** 2026-02-21
**Domain:** Kanidm Admin REST API + Next.js data table + FastAPI proxy layer
**Confidence:** MEDIUM (Kanidm REST API documentation is sparse; core patterns verified from source code)

## Summary

Phase 2 requires building a user management interface where admins can create, list, deactivate/reactivate, change roles, and trigger password resets for users -- all without touching the Kanidm admin console. The central technical challenge is **how the WebUI communicates with Kanidm for administrative operations**. Kanidm exposes a REST API at `/v1/person/*` and `/v1/group/*` endpoints that support all required CRUD operations, but this API requires a privileged service account token (not the logged-in user's OIDC token). The architecture must therefore include a **FastAPI proxy layer** that authenticates admin requests via the user's OIDC token, then forwards them to Kanidm using a pre-configured service account API token with read-write permissions.

The frontend side uses patterns already established in Phase 1: Next.js 16 with Server Components, shadcn/ui components, and bilingual (BG/EN) support via next-intl. The new pieces are: (1) a data table using @tanstack/react-table for the user list with pagination, filtering, and sorting, (2) modal dialogs for user creation, (3) alert dialogs for destructive action confirmations, (4) Sonner toast notifications for operation feedback, and (5) a user detail page at `/users/:id`. These all use standard shadcn/ui components.

The "last login" requirement (USER-06) is the trickiest: Kanidm does not expose a per-user "last login" attribute via its admin API. The practical approach is to track the `auth_time` claim from OIDC tokens in a local database table, updating it each time a user authenticates through the WebUI or QGIS plugin.

**Primary recommendation:** Create a dedicated Kanidm service account (`fiberq_svc`) in `idm_people_admins` + `idm_group_admins`, generate a read-write API token, and build a FastAPI `/users/*` router that proxies all management operations to Kanidm's `/v1/person/*` and `/v1/group/*` REST API. Track last login in a local `user_logins` table.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Data table (dense table) matching the data-dense style from Phase 1
- Columns: Name, Email, Role, Status, Last Login, Actions (buttons)
- Text search by name/email + dropdown filters for role and status (active/inactive)
- Pagination -- expected 50-200 users in the system
- Deactivated users: dimmed row + red "Inactive" badge
- Create user: Modal dialog (from "New User" button above table)
- Fields: Username, Display name, Email, Phone (optional), Role(s)
- Multiple roles -- a user can have more than 1 role (Admin, PM, Designer, Field Worker)
- Combination: quick actions from table + detail page /users/:id on row click
- Detail page shows: profile data, roles, status, actions, projects section (placeholder until Phase 3)
- Confirmation dialog for destructive actions (deactivate, password reset)
- Bilingual messages (BG/EN) -- all dialogs, buttons, notifications translated in both languages

### Claude's Discretion
- Post-creation flow: temporary password or email invite -- based on Kanidm API capabilities
- Distribution of actions between table and detail page
- Notification pattern (toast, inline, or combination)
- Error handling for Kanidm API errors (duplicate, network issue)
- Exact pagination size and style

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.x | Data table with sorting, filtering, pagination | De facto standard for React tables; shadcn/ui data-table guide uses it |
| sonner | 2.x | Toast notifications | shadcn/ui's recommended toast; replaced deprecated Toast component |
| zod | 3.24.x | Form validation schemas | Already in ecosystem (Phase 1 concern); shadcn/ui form standard |
| react-hook-form | 7.x | Form state management | shadcn/ui Form component built on top of it |
| @hookform/resolvers | 4.x | Zod-to-RHF bridge | Connects Zod schemas to react-hook-form |

### Supporting (shadcn/ui components to add)
| Component | Purpose | When to Use |
|-----------|---------|-------------|
| table | Base table markup | Data table rendering |
| dialog | Modal overlays | Create user form |
| alert-dialog | Destructive confirmations | Deactivate user, reset password |
| form | Form fields with validation | Create/edit user forms |
| label | Form field labels | Inside form components |
| select | Dropdown menus | Role filter, role selection |
| sonner | Toast provider | Success/error notifications |
| dropdown-menu | Action menus | Quick actions in table rows |
| badge | Status/role indicators | Active/Inactive status, role chips |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @tanstack/react-table | Plain HTML table | No built-in sorting/filtering/pagination; would need custom implementation |
| sonner | shadcn/ui toast (deprecated) | Toast component is deprecated in shadcn; Sonner is the replacement |
| Server Actions | Client-side fetch | Server Actions keep Kanidm token server-side; no exposure to browser |

**Installation:**
```bash
# In web/ directory
npm install @tanstack/react-table sonner zod react-hook-form @hookform/resolvers

# shadcn/ui components
npx shadcn@latest add table dialog alert-dialog form label select sonner dropdown-menu
```

## Architecture Patterns

### Recommended Project Structure (new/modified files for Phase 2)
```
web/src/
├── app/[locale]/
│   └── users/
│       ├── page.tsx              # User list with data table (replace placeholder)
│       ├── [id]/
│       │   └── page.tsx          # User detail page
│       └── _components/          # Co-located user components
│           ├── columns.tsx       # TanStack table column definitions
│           ├── data-table.tsx    # Reusable data table wrapper
│           ├── user-actions.tsx  # Quick action dropdown for table rows
│           ├── create-user-dialog.tsx  # Modal form for new user
│           └── confirm-dialog.tsx     # Reusable confirmation dialog
├── lib/
│   └── api.ts                    # Extend with user management fetchers
├── messages/
│   ├── en.json                   # Add users.* translation keys
│   └── bg.json                   # Add users.* translation keys
└── types/
    └── user.ts                   # User type definitions

server/api/
├── users/                        # NEW module
│   ├── __init__.py
│   ├── models.py                 # Pydantic models for user CRUD
│   ├── routes.py                 # FastAPI router proxying to Kanidm
│   └── kanidm_client.py          # Kanidm REST API client (httpx)
├── config.py                     # Add KANIDM_API_TOKEN setting
└── main.py                       # Register users router

server/db/
└── init.sql                      # Add user_logins table for last-login tracking
```

### Pattern 1: FastAPI Proxy to Kanidm Admin API

**What:** FastAPI endpoints that authenticate the admin user via their OIDC token, then call Kanidm's REST API using a privileged service account token.
**When to use:** Every user management operation.
**Why:** The logged-in user's OIDC access token cannot call Kanidm's admin API (it's an OAuth2 token, not a Kanidm session token). A service account API token with read-write permissions is required.

```python
# server/api/users/kanidm_client.py
import httpx
from config import settings

class KanidmAdminClient:
    """Client for Kanidm REST API using service account token."""

    def __init__(self):
        self.base_url = settings.kanidm_url
        self.token = settings.kanidm_api_token
        self.verify_tls = settings.kanidm_verify_tls

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def list_persons(self) -> list[dict]:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def create_person(self, username: str, display_name: str) -> dict:
        # POST /v1/person with ProtoEntry body
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.post(
                f"{self.base_url}/v1/person",
                headers=self._headers(),
                json={"attrs": {
                    "name": [username],
                    "displayname": [display_name],
                }},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_person(self, id: str) -> dict:
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person/{id}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def set_person_attr(self, id: str, attr: str, values: list[str]):
        """PUT /v1/person/{id}/_attr/{attr}"""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.put(
                f"{self.base_url}/v1/person/{id}/_attr/{attr}",
                headers=self._headers(),
                json=values,
            )
            resp.raise_for_status()

    async def set_account_expire(self, id: str, expire_value: str):
        """Deactivate: PUT account_expire to 'epoch'. Reactivate: clear it."""
        await self.set_person_attr(id, "account_expire", [expire_value])

    async def clear_account_expire(self, id: str):
        """Remove expiry to reactivate."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.delete(
                f"{self.base_url}/v1/person/{id}/_attr/account_expire",
                headers=self._headers(),
            )
            resp.raise_for_status()

    async def create_credential_reset_token(self, id: str, ttl: int = 3600) -> str:
        """GET /v1/person/{id}/_credential/_update_intent/{ttl}"""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.get(
                f"{self.base_url}/v1/person/{id}/_credential/_update_intent/{ttl}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()  # Returns credential reset token

    async def add_group_member(self, group_name: str, member_id: str):
        """POST /v1/group/{group_name}/_attr/member with member values."""
        async with httpx.AsyncClient(verify=self.verify_tls) as client:
            resp = await client.post(
                f"{self.base_url}/v1/group/{group_name}/_attr/member",
                headers=self._headers(),
                json=[member_id],
            )
            resp.raise_for_status()

    async def remove_group_member(self, group_name: str, member_id: str):
        # This requires reading current members, removing one, then PUT
        pass  # Implementation detail for planner
```

### Pattern 2: Server Actions for User Operations

**What:** Next.js Server Actions call the FastAPI proxy endpoints. Keeps all tokens server-side.
**When to use:** All form submissions and mutation operations from the WebUI.

```typescript
// web/src/app/[locale]/users/_actions.ts
"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";

export async function createUser(formData: {
  username: string;
  displayName: string;
  email: string;
  phone?: string;
  roles: string[];
}) {
  const result = await apiFetch("/users", {
    method: "POST",
    body: JSON.stringify(formData),
  });

  revalidatePath("/[locale]/users");
  return result;
}

export async function deactivateUser(userId: string) {
  const result = await apiFetch(`/users/${userId}/deactivate`, {
    method: "POST",
  });

  revalidatePath("/[locale]/users");
  return result;
}
```

### Pattern 3: TanStack Data Table with Server-Side Data

**What:** Use @tanstack/react-table for client-side sorting/filtering of server-fetched data.
**When to use:** The user list page. With 50-200 users, all data fits in a single fetch.

```typescript
// web/src/app/[locale]/users/_components/columns.tsx
"use client";

import { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { UserActions } from "./user-actions";

export type UserRow = {
  id: string;
  username: string;
  displayName: string;
  email: string;
  roles: string[];
  isActive: boolean;
  lastLogin: string | null;
};

export const columns: ColumnDef<UserRow>[] = [
  {
    accessorKey: "displayName",
    header: "Name", // Will be i18n key
    cell: ({ row }) => (
      <div className={row.original.isActive ? "" : "opacity-50"}>
        {row.original.displayName}
      </div>
    ),
  },
  {
    accessorKey: "email",
    header: "Email",
  },
  {
    accessorKey: "roles",
    header: "Role",
    cell: ({ row }) => (
      <div className="flex gap-1">
        {row.original.roles.map((r) => (
          <Badge key={r} variant="secondary">{r}</Badge>
        ))}
      </div>
    ),
  },
  {
    accessorKey: "isActive",
    header: "Status",
    cell: ({ row }) => (
      <Badge variant={row.original.isActive ? "default" : "destructive"}>
        {row.original.isActive ? "Active" : "Inactive"}
      </Badge>
    ),
  },
  {
    accessorKey: "lastLogin",
    header: "Last Login",
  },
  {
    id: "actions",
    cell: ({ row }) => <UserActions user={row.original} />,
  },
];
```

### Pattern 4: Last Login Tracking

**What:** Store last login timestamps in a local PostgreSQL table since Kanidm does not expose this.
**When to use:** Track logins from both WebUI (via auth.ts callback) and QGIS plugin (via auth endpoint).

```sql
-- server/db/init.sql (add to existing file)
CREATE TABLE user_logins (
    user_sub TEXT PRIMARY KEY,
    last_login_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    login_source TEXT  -- 'web' or 'qgis'
);
CREATE INDEX idx_user_logins_last ON user_logins (last_login_at);
```

```python
# Update in auth routes or middleware
async def record_login(user_sub: str, source: str, pool):
    await pool.execute("""
        INSERT INTO user_logins (user_sub, last_login_at, login_source)
        VALUES ($1, NOW(), $2)
        ON CONFLICT (user_sub) DO UPDATE
        SET last_login_at = NOW(), login_source = $2
    """, user_sub, source)
```

### Anti-Patterns to Avoid
- **Using the user's OIDC access token to call Kanidm admin API:** The OIDC token is for authentication, not administration. Kanidm's admin endpoints require a service account API token.
- **Storing Kanidm service account token in the browser:** The token must stay server-side (in FastAPI env vars). Never expose it to the client.
- **Building server-side pagination for 50-200 users:** Client-side pagination with @tanstack/react-table is simpler and sufficient for this data volume. Fetch all users once, paginate/filter in the browser.
- **Attempting to set passwords directly:** Kanidm does not support setting passwords for users via the admin API. The only mechanism is credential reset tokens that the user redeems interactively.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data table sorting/filtering | Custom sort/filter logic | @tanstack/react-table | Column sorting, text filter, pagination all built-in; proven at scale |
| Toast notifications | Custom notification system | Sonner (via shadcn) | Accessible, auto-dismiss, promise-aware, mobile-optimized |
| Confirmation dialogs | Custom modal | shadcn/ui AlertDialog | Accessible, focus-trapped, keyboard-navigable |
| Form validation | Manual field checking | Zod + react-hook-form | Type-safe schemas, automatic error messages, shadcn Form integration |
| Kanidm API client | Custom HTTP wrappers | httpx AsyncClient class | Already used in project for OIDC; async, connection pooling, TLS config |

**Key insight:** The Kanidm REST API is the real complexity here. The frontend is standard CRUD UI. Focus engineering effort on getting the Kanidm proxy layer right and tested.

## Common Pitfalls

### Pitfall 1: OIDC Token vs Kanidm Admin Token Confusion
**What goes wrong:** Trying to use the logged-in user's OAuth2 access token to call Kanidm's `/v1/person/*` endpoints. Returns 401.
**Why it happens:** Kanidm's admin API authenticates via service account API tokens, not OIDC bearer tokens. The OIDC flow and the admin REST API are separate authentication domains.
**How to avoid:** Create a dedicated service account (`fiberq_svc`), add it to `idm_people_admins` and `idm_group_admins`, generate a read-write API token, store it as `KANIDM_API_TOKEN` env var in the FastAPI container.
**Warning signs:** 401 errors from Kanidm when trying admin operations with the user's session token.

### Pitfall 2: Kanidm ProtoEntry Request Format
**What goes wrong:** Sending a flat JSON object to `POST /v1/person`. Returns 400 or unexpected behavior.
**Why it happens:** Kanidm's create/patch endpoints expect a `ProtoEntry` format where attributes are `{ "attrs": { "name": ["value"], "displayname": ["value"] } }` -- all values are arrays of strings, even for single-value attributes.
**How to avoid:** Always wrap attribute values in arrays. The `attrs` key is required.
**Warning signs:** 400 Bad Request or "invalid entry" errors from Kanidm.

### Pitfall 3: Account Deactivation Mechanism
**What goes wrong:** Looking for a "disable" or "lock" endpoint that does not exist.
**Why it happens:** Kanidm does not have a boolean "active/inactive" flag. Instead, account validity is controlled via `account_expire` and `account_valid_from` datetime attributes.
**How to avoid:** To deactivate: `PUT /v1/person/{id}/_attr/account_expire` with `["1970-01-01T00:00:00+00:00"]` (epoch). To reactivate: `DELETE /v1/person/{id}/_attr/account_expire` to clear the attribute.
**Warning signs:** User can still log in after "deactivation" if the wrong attribute is set.

### Pitfall 4: Password Reset is Not Password Set
**What goes wrong:** Trying to set a user's password directly via the admin API.
**Why it happens:** Many IdPs allow admins to set temporary passwords. Kanidm does not -- by design. Kanidm only allows generating a credential reset token that the user must redeem interactively.
**How to avoid:** Use `GET /v1/person/{id}/_credential/_update_intent/{ttl}` to generate a reset token (valid up to 24h). Display this token to the admin, who provides it to the user. The user visits the Kanidm UI and enters the token to set their own password.
**Warning signs:** No endpoint for `PUT /v1/person/{id}/password`.

### Pitfall 5: Role Management via Group Membership
**What goes wrong:** Looking for a "roles" attribute on the person object.
**Why it happens:** Kanidm does not have a "roles" concept. FiberQ roles are implemented as Kanidm group memberships (fiberq_admin, fiberq_project_manager, etc.).
**How to avoid:** To change a user's role: add/remove them from the appropriate `fiberq_*` groups using `POST /v1/group/{group_name}/_attr/member` and reading/modifying the member list.
**Warning signs:** Searching for role attributes on person objects and finding nothing.

### Pitfall 6: Missing Last Login Data from Kanidm
**What goes wrong:** Expecting Kanidm to provide last login timestamps per user via its admin API.
**Why it happens:** Kanidm's admin API does not expose `auth_time` or last login as a queryable attribute on person objects.
**How to avoid:** Track last login in a local `user_logins` PostgreSQL table. Update it from: (1) the FastAPI auth endpoint when QGIS plugin authenticates, and (2) a Next.js Server Action or API route that records login time when users authenticate via the WebUI. Join this data when serving the user list.
**Warning signs:** Empty "Last Login" column for all users.

### Pitfall 7: TLS Certificate Verification with Kanidm
**What goes wrong:** httpx calls to Kanidm fail with SSL certificate errors in the Docker container.
**Why it happens:** Kanidm often uses self-signed certificates in non-production setups. The httpx client defaults to strict TLS verification.
**How to avoid:** The existing `settings.kanidm_verify_tls` flag is already in config.py. Pass it to the httpx client: `httpx.AsyncClient(verify=settings.kanidm_verify_tls)`. Set `KANIDM_VERIFY_TLS=false` in development only.
**Warning signs:** SSL handshake failures, certificate validation errors from httpx.

## Code Examples

### Kanidm Service Account Setup (CLI)

```bash
# 1. Create a service account for FiberQ user management
kanidm service-account create fiberq_svc "FiberQ User Management Service" idm_admin --name admin

# 2. Add the service account to required admin groups
kanidm group add-members idm_people_admins fiberq_svc --name admin
kanidm group add-members idm_group_admins fiberq_svc --name admin

# 3. Generate a read-write API token (valid until revoked)
kanidm service-account api-token generate fiberq_svc "webui-management" --readwrite --name admin
# Outputs: a bearer token string -- save this as KANIDM_API_TOKEN

# 4. (Optional) Add to idm_people_on_boarding for credential reset tokens
kanidm group add-members idm_people_on_boarding fiberq_svc --name admin
```

### FastAPI User Routes

```python
# server/api/users/routes.py
from fastapi import APIRouter, Depends, HTTPException
from auth.kanidm import get_current_user
from auth.models import UserInfo
from auth.roles import require_admin
from users.models import UserCreate, UserOut, UserListOut
from users.kanidm_client import KanidmAdminClient
from database import get_pool

router = APIRouter()
kanidm = KanidmAdminClient()

@router.get("", response_model=UserListOut)
async def list_users(user: UserInfo = Depends(require_admin)):
    """List all persons from Kanidm, enriched with last login data."""
    persons = await kanidm.list_persons()
    pool = get_pool()

    # Fetch last login times from local db
    logins = await pool.fetch("SELECT user_sub, last_login_at FROM fiberq.user_logins")
    login_map = {row["user_sub"]: row["last_login_at"] for row in logins}

    users = []
    for person in persons:
        attrs = person.get("attrs", {})
        uuid = _first(attrs.get("uuid", []))
        groups = attrs.get("memberof", [])
        roles = [g[len("fiberq_"):] for g in groups
                 if isinstance(g, str) and g.startswith("fiberq_")]

        is_active = "account_expire" not in attrs
        users.append(UserOut(
            id=uuid,
            username=_first(attrs.get("name", [])),
            displayName=_first(attrs.get("displayname", [])),
            email=_first(attrs.get("mail", [])),
            roles=roles,
            isActive=is_active,
            lastLogin=login_map.get(uuid),
        ))

    return UserListOut(users=users)

@router.post("", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, user: UserInfo = Depends(require_admin)):
    """Create a new person in Kanidm and assign to role groups."""
    # 1. Create person
    await kanidm.create_person(body.username, body.displayName)

    # 2. Set additional attributes (mail, phone)
    if body.email:
        await kanidm.set_person_attr(body.username, "mail", [body.email])

    # 3. Add to role groups
    for role in body.roles:
        group_name = f"fiberq_{role}"
        await kanidm.add_group_member(group_name, body.username)

    # 4. Generate credential reset token for initial password setup
    reset_token = await kanidm.create_credential_reset_token(body.username)

    return UserOut(
        id=body.username,
        username=body.username,
        displayName=body.displayName,
        email=body.email,
        roles=body.roles,
        isActive=True,
        resetToken=reset_token,
    )

def _first(lst: list, default: str = "") -> str:
    return lst[0] if lst else default
```

### Create User Dialog Component

```typescript
// web/src/app/[locale]/users/_components/create-user-dialog.tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger
} from "@/components/ui/dialog";
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";
import { createUser } from "../_actions";
import { toast } from "sonner";

const schema = z.object({
  username: z.string().min(2).max(64),
  displayName: z.string().min(1).max(256),
  email: z.string().email(),
  phone: z.string().optional(),
  roles: z.array(z.string()).min(1),
});

type FormValues = z.infer<typeof schema>;

export function CreateUserDialog() {
  const t = useTranslations("users");
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", displayName: "", email: "", roles: [] },
  });

  async function onSubmit(data: FormValues) {
    try {
      const result = await createUser(data);
      toast.success(t("createSuccess"));
      // Show reset token to admin if returned
      if (result.resetToken) {
        // Display in a follow-up dialog
      }
    } catch (error) {
      toast.error(t("createError"));
    }
  }

  // Form JSX with shadcn Form components...
}
```

### Confirmation Dialog for Destructive Actions

```typescript
// Reusable pattern using shadcn/ui AlertDialog
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

function DeactivateConfirm({ userName, onConfirm }: Props) {
  const t = useTranslations("users");
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm">
          {t("deactivate")}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("confirmDeactivateTitle")}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("confirmDeactivateDescription", { name: userName })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm} className="bg-destructive">
            {t("confirmDeactivate")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

## Kanidm REST API Reference

### Person Endpoints (verified from source code)
| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|-------------|
| `/v1/person` | GET | List all persons | None |
| `/v1/person` | POST | Create new person | `{ "attrs": { "name": ["username"], "displayname": ["Display Name"] } }` |
| `/v1/person/{id}` | GET | Get person details | None |
| `/v1/person/{id}` | DELETE | Delete person | None |
| `/v1/person/{id}` | PATCH | Update person | ProtoEntry with changed attrs |
| `/v1/person/{id}/_attr/{attr}` | GET | Get attribute value | None |
| `/v1/person/{id}/_attr/{attr}` | PUT | Set attribute value | `["value1", "value2"]` |
| `/v1/person/{id}/_attr/{attr}` | POST | Append attribute value | `["value"]` |
| `/v1/person/{id}/_attr/{attr}` | DELETE | Remove attribute | None |
| `/v1/person/{id}/_credential/_status` | GET | Check credential status | None |
| `/v1/person/{id}/_credential/_update_intent` | GET | Generate reset token (1h) | None |
| `/v1/person/{id}/_credential/_update_intent/{ttl}` | GET | Generate reset token (custom TTL, max 24h) | None |

### Group Endpoints (verified from source code)
| Endpoint | Method | Purpose | Request Body |
|----------|--------|---------|-------------|
| `/v1/group` | GET | List all groups | None |
| `/v1/group/{id}` | GET | Get group details | None |
| `/v1/group/{id}/_attr/member` | POST | Add member(s) | `["member_id"]` |
| `/v1/group/{id}/_attr/member` | PUT | Set member list | `["member1", "member2"]` |
| `/v1/group/{id}/_attr/member` | GET | Get member list | None |

### Key Attributes for Person Management
| Attribute | Type | Purpose |
|-----------|------|---------|
| `name` | String[] | Username (unique) |
| `displayname` | String[] | Display name |
| `legalname` | String[] | Legal/full name |
| `mail` | String[] | Email address(es) |
| `memberof` | String[] | Group memberships (read-only, computed) |
| `account_expire` | DateTime[] | Account expiry (set to epoch to deactivate) |
| `account_valid_from` | DateTime[] | Account valid from date |
| `uuid` | UUID[] | Unique identifier (permanent, read-only) |

### Authentication
All admin API calls use: `Authorization: Bearer <service_account_api_token>`

## Discretion Recommendations

### Post-Creation Flow: Credential Reset Token
**Recommendation:** Generate a credential reset token after creating a new user. Display the token to the admin in a post-creation dialog. The admin gives the token to the user (in person, via secure channel). The user visits `{KANIDM_URL}/ui/reset` and enters the token to set their password.

**Rationale:** Kanidm does not support email-based password invites natively. Sending email would require an SMTP integration that adds complexity with minimal benefit for 50-200 users. The reset token approach is Kanidm's designed workflow for new user onboarding.

**UI flow:**
1. Admin fills create form, submits
2. Backend creates person, assigns groups, generates reset token
3. Modal shows: "User created. Credential reset token: XXXX-XXXX-XXXX-XXXX (valid for 1 hour). Share this with the user."
4. Copy-to-clipboard button
5. Admin closes dialog, user appears in table

### Action Distribution Between Table and Detail Page
**Recommendation:**

**Table quick actions (via dropdown menu on each row):**
- Deactivate / Reactivate (toggle based on current status)
- Reset Password (generates credential reset token)

**Detail page actions:**
- All table actions plus:
- Edit roles (add/remove role assignments)
- View credential status
- View full profile information
- Projects section (placeholder for Phase 3)

**Rationale:** Deactivate and password reset are the most common admin emergency actions. They should be accessible from the table without navigation. Role changes are less frequent and benefit from seeing the full user context.

### Notification Pattern: Toast (Sonner)
**Recommendation:** Use Sonner toast notifications for all operation feedback.

- **Success:** Green toast with brief message (e.g., "User created", "User deactivated")
- **Error:** Red toast with error detail (e.g., "Failed to create user: username already exists")
- **Info:** Default toast for non-critical info (e.g., "Reset token copied to clipboard")
- **Duration:** 4 seconds for success, 8 seconds for errors (user needs time to read)

**Rationale:** Toasts are non-blocking, auto-dismiss, and work well with the data-dense UI style. They do not obscure the table. Inline errors would add visual noise to the compact layout.

### Error Handling for Kanidm API Errors
**Recommendation:** Map Kanidm HTTP status codes to user-friendly bilingual messages:

| Kanidm Error | HTTP Status | User Message (EN) | User Message (BG) |
|-------------|-------------|--------------------|--------------------|
| Duplicate username | 409 Conflict | "Username already exists" | "Потребителското име вече съществува" |
| Person not found | 404 | "User not found" | "Потребителят не е намерен" |
| Permission denied | 403 | "Insufficient permissions" | "Недостатъчни права" |
| Network error | 502/503 | "Identity service unavailable" | "Услугата за идентификация не е налична" |
| Invalid data | 400 | "Invalid user data" | "Невалидни данни" |

Wrap all Kanidm client calls in try/except, convert httpx errors to FastAPI HTTPExceptions with meaningful detail messages.

### Pagination Size and Style
**Recommendation:** 20 users per page with simple Previous/Next navigation and a page size selector (10/20/50).

**Rationale:** With 50-200 total users and client-side pagination, 20 per page provides a good balance -- enough density to scan quickly, few enough pages to be manageable. The page size selector lets power users increase density.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| shadcn/ui Toast | Sonner | 2024-2025 | Toast component deprecated in shadcn; use Sonner |
| Manual form validation | Zod + react-hook-form | Established | Type-safe server+client validation from one schema |
| Zitadel Management API | Kanidm REST API | Phase 1 migration | Different auth model (service account tokens vs PATs) |
| Direct IdP password set | Credential reset tokens | Kanidm design | Cannot set passwords for users; only generate reset tokens |

**Deprecated/outdated:**
- shadcn/ui `Toast` component: deprecated in favor of Sonner
- Zitadel Management API references in planning docs: project migrated to Kanidm

## Open Questions

1. **Kanidm ProtoEntry Exact Format for POST /v1/person**
   - What we know: Source code shows the body type is `ProtoEntry`, likely `{ "attrs": { "key": ["value"] } }`
   - What's unclear: The exact required vs optional fields for creating a person. The OpenAPI spec on the Kanidm instance (`/docs/v1/openapi.json`) would confirm this.
   - Recommendation: During implementation, fetch the OpenAPI spec from the Kanidm instance at `https://idm.vti.bg/docs/v1/openapi.json` and verify the exact schema. Start with `name` and `displayname` which are the fields the CLI uses.
   - **Confidence:** LOW -- format inferred from source code, not verified against actual API

2. **Group Member Removal Endpoint Behavior**
   - What we know: Groups have `POST /v1/group/{id}/_attr/member` to add and `PUT` to replace. There is a `DELETE /v1/group/{id}/_attr/member` that removes the entire member list.
   - What's unclear: How to remove a single member without clearing all members. May need to GET current members, filter out the target, then PUT the remaining list.
   - Recommendation: Test on the actual Kanidm instance. If single-member removal is not supported atomically, use the GET-filter-PUT pattern.
   - **Confidence:** LOW -- needs validation against actual Kanidm behavior

3. **Kanidm Person List Response Format**
   - What we know: `GET /v1/person` returns a list. Each entry has `attrs` with attribute arrays.
   - What's unclear: Whether `memberof` (group memberships) is included in the list response or only in individual `GET /v1/person/{id}` responses. If not included, we need N+1 queries or a different approach to show roles in the table.
   - Recommendation: Test the list endpoint response. If `memberof` is missing from list, either (a) fetch all persons individually (acceptable for 50-200 users), or (b) fetch all fiberq_* groups and their members to build a role map.
   - **Confidence:** LOW -- needs actual API testing

4. **Credential Reset Token Format**
   - What we know: CLI shows tokens like `8qDRG-AE1qC-zjjAT-0Fkd6`. The REST API endpoint returns JSON.
   - What's unclear: The exact JSON structure returned by `GET /v1/person/{id}/_credential/_update_intent/{ttl}`. Is it `{ "token": "..." }` or a different format?
   - Recommendation: Test the endpoint on the live Kanidm instance during implementation.
   - **Confidence:** LOW -- format not documented in public docs

5. **Designer Role Group**
   - What we know: CONTEXT.md mentions "Admin, PM, Designer, Field Worker" as roles. Phase 1 defined 4 roles: admin, project_manager, engineer, field_worker.
   - What's unclear: Whether "Designer" maps to the existing "engineer" role or if a new `fiberq_designer` group needs to be created in Kanidm.
   - Recommendation: Clarify with user. If "Designer" is a new role, create `fiberq_designer` group. If it maps to "engineer", use the existing group. For planning purposes, assume the existing 4 roles from Phase 1 unless told otherwise.
   - **Confidence:** MEDIUM -- likely "Designer" = "engineer" based on Phase 1 context

## Sources

### Primary (HIGH confidence)
- Kanidm source code (v1.rs routes): https://github.com/kanidm/kanidm/blob/master/server/core/src/https/v1.rs -- all REST API routes verified
- Kanidm People Accounts docs: https://kanidm.github.io/kanidm/stable/accounts/people_accounts.html -- account create, validity, attributes
- Kanidm Groups docs: https://kanidm.github.io/kanidm/stable/accounts/groups.html -- group membership management
- Kanidm Service Accounts docs: https://kanidm.github.io/kanidm/stable/accounts/service_accounts.html -- API token generation
- Kanidm Authentication & Credentials docs: https://kanidm.github.io/kanidm/stable/accounts/authentication_and_credentials.html -- credential reset flow
- shadcn/ui Data Table: https://ui.shadcn.com/docs/components/radix/data-table -- TanStack React Table integration
- shadcn/ui AlertDialog: https://ui.shadcn.com/docs/components/radix/alert-dialog -- confirmation dialogs
- shadcn/ui Sonner: https://ui.shadcn.com/docs/components/radix/sonner -- toast notifications

### Secondary (MEDIUM confidence)
- Kanidm credential reset discussion: https://github.com/kanidm/kanidm/discussions/2537 -- REST API credential flow
- Kanidm person data retrieval discussion: https://github.com/kanidm/kanidm/discussions/2709 -- admin API auth clarification
- DeepWiki Kanidm API reference: https://deepwiki.com/kanidm/kanidm/2.5-web-ui-and-api -- API endpoint listing
- Kanidm REST API issue: https://github.com/kanidm/kanidm/issues/2951 -- API documentation gaps, auth flow

### Tertiary (LOW confidence)
- Kanidm ProtoEntry format: inferred from source code, not verified against live API
- Group member removal: inferred from attribute endpoint pattern, not tested
- Person list response completeness: assumed similar to individual GET, not verified

## Metadata

**Confidence breakdown:**
- Standard stack (frontend): HIGH -- shadcn/ui + TanStack Table is well-documented, established pattern
- Architecture (proxy pattern): HIGH -- standard approach for IdP management APIs, same pattern used in Zitadel era
- Kanidm REST API endpoints: MEDIUM -- routes verified from source code, but request/response formats need validation on live instance
- Kanidm ProtoEntry format: LOW -- inferred, not documented publicly
- Last login tracking: MEDIUM -- local table approach is straightforward but adds a data source to maintain

**Research date:** 2026-02-21
**Valid until:** 2026-03-07 (7 days -- Kanidm API details need live validation early)

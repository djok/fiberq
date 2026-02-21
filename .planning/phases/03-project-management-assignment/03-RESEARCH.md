# Phase 3: Project Management & Assignment - Research

**Researched:** 2026-02-21
**Domain:** FastAPI project CRUD + PostGIS bounding box queries + MapLibre GL JS mini-maps + Next.js role-scoped views + shadcn/ui card grid
**Confidence:** HIGH (frontend patterns established in Phase 2; backend is standard CRUD on existing tables; mini-map is new but well-documented)

## Summary

Phase 3 builds project management and user-to-project assignment on top of the existing infrastructure. The backend already has a `projects` table with `bounds_geom GEOMETRY(Polygon, 4326)`, a `/projects` FastAPI router with basic CRUD, and all infrastructure tables (`ftth_okna`, `ftth_stubovi`, `ftth_kablovi_*`, etc.) already reference `project_id`. The core backend work is: (1) add a `project_users` junction table for assignment with project-level roles, (2) add a `status` column to projects, (3) extend the existing routes with role-based visibility filtering, and (4) add assignment endpoints. The frontend replaces the placeholder projects page with a card-grid layout, each card showing project name, status badge, member count, and a PostGIS-driven mini-map rendered via MapLibre GL JS.

The user decided on card-based layout (not a table), with mini-maps showing geographic visualization from PostGIS data. This is the most technically novel piece: each card renders a small, non-interactive MapLibre GL map that displays the project's bounding box or computed extent from infrastructure features. The backend computes this extent using PostGIS `ST_Extent` aggregate across all infrastructure tables for a given project, returns it as GeoJSON, and the frontend renders it on a lightweight map tile background.

For assignment, the user chose an inline combobox directly in the members section (not a dialog), with project-level roles: Manager / Specialist / Observer. The Combobox in Radix-based shadcn/ui projects is built using Command + Popover composition pattern (not the newer Base UI native combobox, which has no Radix implementation). The `cmdk` package and `popover` component need to be added.

**Primary recommendation:** Extend the existing `projects` API module with `status` field, `project_users` junction table, role-scoped list queries, and a `/projects/{id}/extent` endpoint returning GeoJSON bounding box computed via PostGIS. Frontend: card grid with MapLibre GL mini-maps, inline Combobox for member assignment, and modal dialog for project creation (same pattern as user creation in Phase 2).

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Card-based layout (not table) -- grid of cards for visual overview
- Each card shows: project name, status, mini-map (geographic visualization from PostGIS data)
- Mini-map extracts bounding box / geometry from existing PostGIS project data
- Statuses: Planning / In Progress / Completed / Paused / Archived (5 levels)
- Filtering and search by name, status, assigned user (from success criteria)
- Inline combobox directly in the members section (not a dialog) for assignment
- Removal via X button next to member name with confirmation
- Project-level roles: Manager / Specialist / Observer (3 levels)
- When assigning, the project role is selected alongside the user
- One user can be in many projects with different roles
- Project creation via modal dialog (same as user creation in Phase 2)
- Admin sees all projects
- Project Manager (global role) sees all projects (but fewer permissions than Admin)
- Specialist and Field Worker see only projects they are assigned to
- Assignment: Admin + project managers (users with Manager role in that specific project)
- Project creation: Admin + Project Manager (global role)
- Empty state for non-admin without projects: message "You have no assigned projects. Contact an administrator."

### Claude's Discretion
- Layout of the project detail page (map + sidebar, sections, or tabs)
- Content of the project detail page (basic info + map + members as minimum)
- Fields when creating a project (at minimum: name + description from success criteria)
- Exact design of cards and mini-map
- Technical details of PostGIS integration for mini-map

### Deferred Ideas (OUT OF SCOPE)
- Full map view of all projects -- separate phase or addition (user mentioned idea for visualizing all projects on a shared map)

</user_constraints>

## Scope Conflict: Mini-Map vs Requirements Out-of-Scope

The requirements document (`REQUIREMENTS.md`) explicitly lists "Project area map preview" as **Out of Scope** for this milestone: "Next milestone; requires map library integration (Leaflet/MapLibre)." However, the user's CONTEXT.md decisions (made after the requirements were written) explicitly include mini-maps on project cards showing PostGIS-driven geographic visualization. **The CONTEXT.md decisions are authoritative** since they represent the user's most recent intent. This research proceeds with the mini-map feature included.

**Impact:** This adds ~1 new dependency (`maplibre-gl` + CSS) and a moderate amount of frontend work (non-interactive map component, GeoJSON overlay). The backend work is minimal since PostGIS functions already exist.

## Status Values Conflict

The requirements doc (PROJ-04) specifies: "Planning, Design, Construction, As-Built, Completed." The CONTEXT.md decisions specify: "Planning / In Progress / Completed / Paused / Archived." **CONTEXT.md is authoritative.** Use the 5 statuses from CONTEXT.md:

| Status | Bulgarian | English |
|--------|-----------|---------|
| planning | Планиране | Planning |
| in_progress | В изпълнение | In Progress |
| completed | Завършен | Completed |
| paused | Паузиран | Paused |
| archived | Архивиран | Archived |

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | App Router, Server Components, Server Actions | Already in project |
| React | 19.2.3 | UI rendering | Already in project |
| shadcn/ui (Radix) | new-york style | Card, Dialog, Badge, Form components | Already in project |
| @tanstack/react-table | 8.21.3 | Could be reused for members list if needed | Already in project |
| react-hook-form | 7.71.2 | Form state for create/edit dialogs | Already in project |
| zod | 4.3.6 | Validation schemas | Already in project |
| sonner | 2.0.7 | Toast notifications | Already in project |
| FastAPI | 0.115.6 | Backend API | Already in project |
| asyncpg | 0.30.0 | PostgreSQL async driver | Already in project |
| PostGIS | 16-3.4 | Spatial database extension | Already in project |

### New Dependencies
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| maplibre-gl | 5.x | Map rendering for mini-maps on cards and detail page | Open-source fork of Mapbox GL JS; free, no API key; the standard for web map rendering |
| cmdk | 1.x | Command palette for Combobox composition | Required by shadcn/ui Command component (Radix variant) |

### shadcn/ui Components to Add
| Component | Purpose | Installation |
|-----------|---------|-------------|
| command | Combobox search/filter in inline assignment | `npx shadcn@latest add command` |
| popover | Combobox dropdown container | `npx shadcn@latest add popover` |
| scroll-area | Scrollable members list | `npx shadcn@latest add scroll-area` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| maplibre-gl | Leaflet | Leaflet is lighter but no vector tile support; MapLibre handles both raster and vector, better for future GIS features |
| maplibre-gl | Static image from server-side rendering | Eliminates client JS but requires running MapLibre GL Native on server, adds Docker complexity |
| Command+Popover combobox | Base UI Combobox | Base UI variant has no Radix implementation in shadcn/ui; would require switching component library |

**Installation:**
```bash
# In web/ directory
npm install maplibre-gl

# shadcn/ui components
npx shadcn@latest add command popover scroll-area
```

## Architecture Patterns

### Recommended Project Structure (new/modified files for Phase 3)
```
server/api/
├── projects/
│   ├── models.py          # MODIFY: add status, ProjectMemberOut, AssignmentCreate, extent models
│   └── routes.py          # MODIFY: add status, visibility filtering, assignment endpoints, extent endpoint
└── db/
    └── init.sql           # MODIFY: add project_users table, status column to projects

web/src/
├── app/[locale]/
│   └── projects/
│       ├── page.tsx              # REPLACE: card grid with filtering (Server Component)
│       ├── [id]/
│       │   └── page.tsx          # NEW: project detail page (Server Component)
│       ├── _components/
│       │   ├── projects-client.tsx    # Client wrapper for card grid + filters
│       │   ├── project-card.tsx       # Single project card with mini-map
│       │   ├── project-mini-map.tsx   # MapLibre GL mini-map component
│       │   ├── create-project-dialog.tsx  # Modal for new project
│       │   ├── project-members.tsx    # Members section with inline combobox
│       │   ├── member-combobox.tsx    # Command+Popover user search/select
│       │   ├── project-detail-actions.tsx # Client component for detail page actions
│       │   └── edit-project-dialog.tsx    # Edit name/description/status
│       └── _actions.ts           # Server Actions for project mutations
├── types/
│   └── project.ts               # NEW: Project, ProjectMember types
└── messages/
    ├── en.json                   # ADD: projects.* translation keys
    └── bg.json                   # ADD: projects.* translation keys
```

### Pattern 1: Role-Scoped Project Listing (Backend)

**What:** The project list endpoint returns different results based on user role. Admin and Project Manager see all projects; others see only projects where they are assigned.
**When to use:** `GET /projects` endpoint.

```python
# server/api/projects/routes.py
@router.get("/", response_model=list[ProjectOut])
async def list_projects(user: UserInfo = Depends(get_current_user)):
    pool = get_pool()

    # Admin and project_manager see all projects
    if user.is_admin or "project_manager" in user.roles:
        rows = await pool.fetch("""
            SELECT p.id, p.name, p.description, p.status, p.created_at, p.created_by_sub,
                   (SELECT COUNT(*) FROM project_users pu WHERE pu.project_id = p.id) as member_count
            FROM projects p
            ORDER BY p.id
        """)
    else:
        # Others see only assigned projects
        rows = await pool.fetch("""
            SELECT p.id, p.name, p.description, p.status, p.created_at, p.created_by_sub,
                   (SELECT COUNT(*) FROM project_users pu WHERE pu.project_id = p.id) as member_count
            FROM projects p
            JOIN project_users pu ON pu.project_id = p.id
            WHERE pu.user_sub = $1
            ORDER BY p.id
        """, user.sub)

    return [ProjectOut(**dict(r)) for r in rows]
```

### Pattern 2: PostGIS Bounding Box Computation

**What:** Compute the geographic extent of all features belonging to a project by aggregating across all infrastructure tables using `ST_Extent`.
**When to use:** To supply bounding box data for mini-maps on project cards.

```python
# server/api/projects/routes.py
@router.get("/{project_id}/extent")
async def get_project_extent(
    project_id: int,
    user: UserInfo = Depends(get_current_user),
):
    """Return the bounding box of all features in this project as GeoJSON."""
    pool = get_pool()

    # Compute extent across all infrastructure tables
    row = await pool.fetchrow("""
        SELECT ST_AsGeoJSON(ST_Envelope(ST_Extent(combined.geom)))::json as extent
        FROM (
            SELECT geom FROM ftth_okna WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_stubovi WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_kablovi_podzemni WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_kablovi_nadzemni WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_trase WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_cevi WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_mufovi WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_spojevi WHERE project_id = $1 AND geom IS NOT NULL
            UNION ALL
            SELECT geom FROM ftth_elements WHERE project_id = $1 AND geom IS NOT NULL
        ) combined
    """, project_id)

    # Fall back to project's own bounds_geom if no features
    if not row or not row["extent"]:
        row = await pool.fetchrow("""
            SELECT ST_AsGeoJSON(bounds_geom)::json as extent
            FROM projects WHERE id = $1
        """, project_id)

    if not row or not row["extent"]:
        return {"extent": None}

    return {"extent": row["extent"]}
```

**Optimization note:** For the card grid listing, computing extent per-project via N separate queries is expensive. Better approach: batch-compute extents in a single query:

```python
# Batch extent for all visible projects (in list endpoint)
rows = await pool.fetch("""
    SELECT project_id,
           ST_AsGeoJSON(ST_Envelope(ST_Extent(geom)))::json as extent
    FROM (
        SELECT project_id, geom FROM ftth_okna WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_stubovi WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_kablovi_podzemni WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_kablovi_nadzemni WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_trase WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_cevi WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_mufovi WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_spojevi WHERE geom IS NOT NULL
        UNION ALL
        SELECT project_id, geom FROM ftth_elements WHERE geom IS NOT NULL
    ) combined
    GROUP BY project_id
""")
extent_map = {r["project_id"]: r["extent"] for r in rows}
```

### Pattern 3: Non-Interactive MapLibre GL Mini-Map Component

**What:** A small, non-interactive map that renders a project's geographic extent as a GeoJSON polygon overlay on free OpenStreetMap tiles.
**When to use:** On each project card in the grid layout.

```typescript
// web/src/app/[locale]/projects/_components/project-mini-map.tsx
"use client";

import { useRef, useEffect } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface ProjectMiniMapProps {
  extent: GeoJSON.Geometry | null;
  className?: string;
}

export function ProjectMiniMap({ extent, className }: ProjectMiniMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || !extent) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },
      interactive: false,
      attributionControl: false,
    });

    map.on("load", () => {
      map.addSource("extent", {
        type: "geojson",
        data: { type: "Feature", geometry: extent, properties: {} },
      });

      map.addLayer({
        id: "extent-fill",
        type: "fill",
        source: "extent",
        paint: {
          "fill-color": "oklch(0.55 0.15 165)",  // primary color
          "fill-opacity": 0.15,
        },
      });

      map.addLayer({
        id: "extent-outline",
        type: "line",
        source: "extent",
        paint: {
          "line-color": "oklch(0.55 0.15 165)",
          "line-width": 2,
        },
      });

      // Fit to extent bounds
      const coords = (extent as GeoJSON.Polygon).coordinates[0];
      const bounds = coords.reduce(
        (b, c) => b.extend(c as [number, number]),
        new maplibregl.LngLatBounds(coords[0] as [number, number], coords[0] as [number, number])
      );
      map.fitBounds(bounds, { padding: 20, animate: false });
    });

    mapRef.current = map;
    return () => map.remove();
  }, [extent]);

  if (!extent) {
    return (
      <div className={cn("bg-muted flex items-center justify-center text-muted-foreground text-xs", className)}>
        No geographic data
      </div>
    );
  }

  return <div ref={containerRef} className={className} />;
}
```

### Pattern 4: Inline Combobox for Member Assignment

**What:** A Command + Popover composition that searches users and allows selecting a user + project role to assign.
**When to use:** In the project detail page members section.

```typescript
// web/src/app/[locale]/projects/_components/member-combobox.tsx
"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList,
} from "@/components/ui/command";
import {
  Popover, PopoverContent, PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

interface User {
  id: string;
  displayName: string;
  email: string;
}

interface MemberComboboxProps {
  users: User[];
  existingMemberIds: string[];
  onAssign: (userId: string, role: string) => Promise<void>;
}

const PROJECT_ROLES = ["manager", "specialist", "observer"] as const;

export function MemberCombobox({ users, existingMemberIds, onAssign }: MemberComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [selectedUser, setSelectedUser] = React.useState<string>("");
  const [selectedRole, setSelectedRole] = React.useState<string>("specialist");

  // Filter out already-assigned users
  const available = users.filter((u) => !existingMemberIds.includes(u.id));

  async function handleAssign() {
    if (!selectedUser || !selectedRole) return;
    await onAssign(selectedUser, selectedRole);
    setSelectedUser("");
    setOpen(false);
  }

  return (
    <div className="flex gap-2 items-center">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open} className="flex-1 justify-between">
            {selectedUser
              ? available.find((u) => u.id === selectedUser)?.displayName
              : "Select user..."}
            <ChevronsUpDown className="opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0">
          <Command>
            <CommandInput placeholder="Search users..." />
            <CommandList>
              <CommandEmpty>No users found.</CommandEmpty>
              <CommandGroup>
                {available.map((user) => (
                  <CommandItem
                    key={user.id}
                    value={user.displayName}
                    onSelect={() => {
                      setSelectedUser(user.id);
                      setOpen(false);
                    }}
                  >
                    <div>
                      <div>{user.displayName}</div>
                      <div className="text-xs text-muted-foreground">{user.email}</div>
                    </div>
                    <Check className={cn("ml-auto", selectedUser === user.id ? "opacity-100" : "opacity-0")} />
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <Select value={selectedRole} onValueChange={setSelectedRole}>
        <SelectTrigger className="w-[140px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {PROJECT_ROLES.map((role) => (
            <SelectItem key={role} value={role}>{role}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button size="sm" onClick={handleAssign} disabled={!selectedUser}>
        Add
      </Button>
    </div>
  );
}
```

### Pattern 5: Server Component with Role-Based Data Fetch

**What:** The projects page is a Server Component that fetches projects via `apiFetch` and passes the data to a client wrapper, following the Phase 2 pattern.
**When to use:** Projects list page and project detail page.

```typescript
// web/src/app/[locale]/projects/page.tsx
import { setRequestLocale, getTranslations } from "next-intl/server";
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { ProjectsClient } from "./_components/projects-client";
import type { ProjectCard } from "@/types/project";

type ApiProject = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  member_count: number;
  extent: object | null;  // GeoJSON geometry or null
  created_at: string;
};

function mapProject(p: ApiProject): ProjectCard {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    status: p.status,
    memberCount: p.member_count,
    extent: p.extent,
    createdAt: p.created_at,
  };
}

export default async function ProjectsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session) {
    redirect(`/${locale}`);
  }

  let projects: ProjectCard[] = [];
  try {
    const data = await apiFetch<ApiProject[]>("/projects");
    projects = data.map(mapProject);
  } catch {
    // API unavailable -- show empty state
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <ProjectsClient projects={projects} locale={locale} />
    </div>
  );
}
```

### Pattern 6: project_users Junction Table

**What:** A junction table linking users to projects with project-level roles, enabling the assignment system.
**When to use:** All assignment operations.

```sql
-- New table to add to init.sql
CREATE TABLE project_users (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_sub TEXT NOT NULL,
    user_display_name TEXT,       -- Denormalized for display without Kanidm lookup
    user_email TEXT,              -- Denormalized for display
    project_role TEXT NOT NULL DEFAULT 'specialist',  -- manager | specialist | observer
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by_sub TEXT,
    UNIQUE (project_id, user_sub)
);
CREATE INDEX idx_project_users_project ON project_users (project_id);
CREATE INDEX idx_project_users_user ON project_users (user_sub);
```

**Denormalization rationale:** User display name and email are stored in Kanidm, not in PostgreSQL. Fetching from Kanidm for every project listing would be expensive and fragile. Denormalizing these fields into `project_users` means the project member list can be served entirely from PostgreSQL. The tradeoff is data can become stale if a user's name/email changes in Kanidm, but this is acceptable for a small team (50-200 users) where name changes are rare.

### Pattern 7: Server Actions for Project Mutations

**What:** Server Actions following the same discriminated union pattern from Phase 2.
**When to use:** All create, update, assign, remove operations.

```typescript
// web/src/app/[locale]/projects/_actions.ts
"use server";

import { apiFetch } from "@/lib/api";
import { revalidatePath } from "next/cache";

type ActionResult<T = void> =
  | { success: true; data: T }
  | { success: false; error: string };

export async function createProject(data: {
  name: string;
  description?: string;
}): Promise<ActionResult<{ id: number }>> {
  try {
    const result = await apiFetch<{ id: number }>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
    revalidatePath("/[locale]/projects");
    return { success: true, data: result };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to create project",
    };
  }
}

export async function assignMember(
  projectId: number,
  userId: string,
  projectRole: string,
): Promise<ActionResult> {
  try {
    await apiFetch(`/projects/${projectId}/members`, {
      method: "POST",
      body: JSON.stringify({ user_sub: userId, project_role: projectRole }),
    });
    revalidatePath("/[locale]/projects/[id]");
    return { success: true, data: undefined };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "Failed to assign member",
    };
  }
}
```

### Anti-Patterns to Avoid
- **Fetching Kanidm user list on every project page load:** The member combobox needs a user list for assignment. Do NOT call Kanidm's list persons endpoint on every project detail page render. Instead, the combobox should trigger a user search only when opened, or prefetch the list once via a cached endpoint.
- **Computing PostGIS extents client-side:** Do NOT send raw coordinates to the frontend for bounding box computation. Use `ST_Extent` + `ST_Envelope` + `ST_AsGeoJSON` on the server side and return finished GeoJSON.
- **Separate API calls per card for extent:** Do NOT make N API calls (one per project) to get extent data for the card grid. Batch-compute all extents in a single query and include them in the project list response.
- **Building a full interactive map component:** The mini-map on cards must be `interactive: false`. Do NOT add navigation controls, zoom handlers, or click events to card mini-maps. Save interactive maps for the detail page or future phases.
- **Using the new Base UI Combobox from shadcn/ui:** The project uses Radix UI (not Base UI). The native Combobox component in shadcn has no Radix implementation. Use the Command + Popover composition pattern instead.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Map rendering | Custom canvas/SVG map drawing | MapLibre GL JS | Handles tile loading, projection, GeoJSON rendering, and zoom levels automatically |
| Geographic bounding box computation | Manual min/max coordinate scanning | PostGIS `ST_Extent` + `ST_Envelope` | Handles all geometry types (Point, LineString, Polygon), NULL values, and CRS correctly |
| GeoJSON serialization | Manual coordinate array building | PostGIS `ST_AsGeoJSON` | Produces spec-compliant GeoJSON; handles all geometry types |
| Searchable dropdown | Custom input + filtered list | shadcn Command + Popover (cmdk) | Keyboard navigation, fuzzy search, accessibility, focus management |
| Confirmation for member removal | Custom modal | Shared `ConfirmActionDialog` from Phase 2 | Already built and tested; reuse across features |
| Status badge colors | Manual CSS per status | Badge variant + utility function | Consistent with existing design system |

**Key insight:** The hardest new technology in this phase is MapLibre GL JS for mini-maps. Everything else is established patterns from Phase 2 (Server Components + Server Actions + shadcn/ui) applied to a new domain (projects instead of users).

## Common Pitfalls

### Pitfall 1: MapLibre GL CSS Not Loaded
**What goes wrong:** Map container renders as empty/invisible because MapLibre's CSS is missing.
**Why it happens:** MapLibre GL JS requires its own CSS file (`maplibre-gl/dist/maplibre-gl.css`) for the map container, controls, and markers to display correctly. Next.js does not auto-import CSS from node_modules.
**How to avoid:** Import the CSS in the mini-map component file: `import "maplibre-gl/dist/maplibre-gl.css";`. Or import it once in a layout file.
**Warning signs:** Map container has 0 height, or map tiles do not render despite no JS errors.

### Pitfall 2: MapLibre GL in Server Components
**What goes wrong:** Build error or "window is not defined" when MapLibre is imported in a Server Component.
**Why it happens:** MapLibre GL JS accesses browser APIs (`window`, `document`, `WebGL`). Server Components run on the server where these do not exist.
**How to avoid:** The mini-map component MUST be a Client Component (`"use client"`). Use dynamic import with `ssr: false` if needed: `const MiniMap = dynamic(() => import("./project-mini-map"), { ssr: false })`.
**Warning signs:** "ReferenceError: window is not defined" during build or server render.

### Pitfall 3: Too Many MapLibre Instances on Card Grid
**What goes wrong:** Page becomes slow or crashes when rendering 20+ project cards, each with its own MapLibre map instance.
**Why it happens:** Each MapLibre Map instance creates a WebGL context. Browsers limit WebGL contexts (typically 8-16 concurrent). Exceeding the limit causes context loss.
**How to avoid:** (a) Use `maplibregl.Map.setMaxListeners` and proper cleanup in useEffect return. (b) Consider lazy-loading maps with Intersection Observer -- only create map instances for cards currently in viewport. (c) For cards outside viewport, show a static placeholder. (d) Alternative: render a static image server-side and only use MapLibre on the detail page.
**Warning signs:** "WARNING: Too many active WebGL contexts" console warnings, maps going black.

### Pitfall 4: N+1 Query for Project Extents
**What goes wrong:** Project list page makes one SQL query per project to compute extent, causing slow page loads.
**Why it happens:** Natural implementation is to loop over projects and fetch extent for each one.
**How to avoid:** Batch-compute all project extents in a single UNION ALL query grouped by `project_id`. Include the extent in the project list response, not as a separate endpoint.
**Warning signs:** Page load time scales linearly with number of projects; visible delay on 20+ projects.

### Pitfall 5: Empty Extent for New Projects
**What goes wrong:** Mini-map renders nothing or errors for a newly created project with no infrastructure features.
**Why it happens:** `ST_Extent` returns NULL when there are no geometries. The GeoJSON serialization chain breaks on NULL.
**How to avoid:** Check for NULL extent and fall back to: (a) the project's `bounds_geom` column if set, (b) a default "no data" placeholder in the UI. The API should return `null` for extent when no data exists, and the frontend should render a "No geographic data" placeholder.
**Warning signs:** JavaScript errors in the mini-map component for projects without features.

### Pitfall 6: Assignment Permission Check Complexity
**What goes wrong:** Permission logic becomes tangled because assignment rights depend on BOTH global role and project-level role.
**Why it happens:** "Admin + project managers (users with Manager role in that specific project)" means the check is: `user.is_admin OR (user is project member AND member.project_role == 'manager')`. This requires a database lookup for the project-level role check.
**How to avoid:** Create a dedicated dependency function:
```python
async def require_project_manager(project_id: int, user: UserInfo) -> UserInfo:
    if user.is_admin:
        return user
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT project_role FROM project_users WHERE project_id = $1 AND user_sub = $2",
        project_id, user.sub
    )
    if row and row["project_role"] == "manager":
        return user
    raise HTTPException(status_code=403, detail="Project manager role required")
```
**Warning signs:** Inconsistent permission behavior between admin and project manager users.

### Pitfall 7: Stale Denormalized User Data in project_users
**What goes wrong:** A user's display name or email is updated in Kanidm, but the `project_users` table still shows the old values.
**Why it happens:** `user_display_name` and `user_email` are denormalized into `project_users` for query efficiency, but never updated after initial assignment.
**How to avoid:** Accept this tradeoff for Phase 3 (small team, rare name changes). Document it as a known limitation. For future improvement, add a periodic sync or update the denormalized fields when the user management page is used.
**Warning signs:** Member list shows outdated names that do not match the user management page.

## Code Examples

### Database Schema Changes

```sql
-- Add status column to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'planning';

-- Create project_users junction table
CREATE TABLE IF NOT EXISTS project_users (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_sub TEXT NOT NULL,
    user_display_name TEXT,
    user_email TEXT,
    project_role TEXT NOT NULL DEFAULT 'specialist'
        CHECK (project_role IN ('manager', 'specialist', 'observer')),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by_sub TEXT,
    UNIQUE (project_id, user_sub)
);
CREATE INDEX IF NOT EXISTS idx_project_users_project ON project_users (project_id);
CREATE INDEX IF NOT EXISTS idx_project_users_user ON project_users (user_sub);
```

### Pydantic Models (Backend)

```python
# server/api/projects/models.py
from datetime import datetime
from pydantic import BaseModel

PROJECT_STATUSES = ["planning", "in_progress", "completed", "paused", "archived"]

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    status: str = "planning"

class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None

class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    status: str
    member_count: int = 0
    extent: dict | None = None  # GeoJSON geometry
    created_at: datetime
    created_by_sub: str | None

class ProjectMemberOut(BaseModel):
    id: int
    user_sub: str
    user_display_name: str | None
    user_email: str | None
    project_role: str
    assigned_at: datetime

class AssignMemberBody(BaseModel):
    user_sub: str
    user_display_name: str | None = None
    user_email: str | None = None
    project_role: str = "specialist"

class ProjectDetailOut(BaseModel):
    """Extended project with members and extent for detail page."""
    id: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    created_by_sub: str | None
    members: list[ProjectMemberOut] = []
    extent: dict | None = None
```

### TypeScript Types (Frontend)

```typescript
// web/src/types/project.ts
export type ProjectCard = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  memberCount: number;
  extent: GeoJSON.Geometry | null;
  createdAt: string;
};

export type ProjectDetail = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  createdAt: string;
  createdBySub: string | null;
  members: ProjectMember[];
  extent: GeoJSON.Geometry | null;
};

export type ProjectMember = {
  id: number;
  userSub: string;
  userDisplayName: string | null;
  userEmail: string | null;
  projectRole: string;
  assignedAt: string;
};

export type CreateProjectInput = {
  name: string;
  description?: string;
};
```

### Free Tile Source Configuration

For mini-maps, use OpenStreetMap raster tiles (free, no API key):

```typescript
// Inline style definition for MapLibre -- no external style.json needed
const MINI_MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "&copy; OpenStreetMap contributors",
    },
  },
  layers: [
    {
      id: "osm-tiles",
      type: "raster",
      source: "osm",
    },
  ],
};
```

**Note:** OpenStreetMap tile usage policy requires attribution and requests usage under 250k tiles/day. For a small internal app, this is fine. For production at scale, consider self-hosting tiles with `tileserver-gl` or using MapTiler with a free tier.

## Discretion Recommendations

### Project Detail Page Layout: Map + Sidebar

**Recommendation:** Two-column layout on desktop (lg breakpoint):
- **Left column (2/3 width):** Larger interactive map showing project extent + info card with name, description, status, creation date
- **Right column (1/3 width):** Members section with inline combobox, project actions card

On mobile/tablet: single column, map on top, then info, then members.

**Rationale:** This mirrors the user detail page pattern from Phase 2 (content left, actions right) while giving prominence to the map, which is the visual centerpiece for a GIS project. The map on the detail page CAN be interactive (unlike card mini-maps) to let users explore the project area.

### Project Detail Page Content

**Recommendation:** Minimum content sections:
1. **Header:** Project name + status badge + back link
2. **Map card:** Interactive MapLibre map with project extent polygon and feature points (larger than card mini-map, ~300-400px height)
3. **Project info card:** Name (editable), description (editable), status (editable dropdown), created at, created by
4. **Members card:** List of assigned members with role badges, inline combobox for adding, X button for removing
5. **Actions card:** Edit project button, archive/pause/delete actions

### Create Project Dialog Fields

**Recommendation:** Minimal fields matching the success criteria + user's status decision:
- **Name** (required) -- text input
- **Description** (optional) -- textarea
- **Status** (optional, defaults to "Planning") -- select dropdown with 5 statuses

**Rationale:** Keep creation simple. Most metadata (members, geographic data) comes from usage after creation. The user specifically wanted a modal dialog like Phase 2's user creation.

### Card Design for Mini-Map Integration

**Recommendation:** Each project card layout:
```
+---------------------------+
| [Mini-map: 100% width,    |
|  ~120px height]            |
+---------------------------+
| Project Name               |
| Status Badge   N members   |
| Short description...       |
+---------------------------+
```

- Mini-map at the top of the card, edge-to-edge (no padding), with rounded top corners matching the card
- Below the map: project name (bold), status badge (color-coded), member count, truncated description
- Card click navigates to detail page
- Grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` for responsive layout

### Status Badge Color Mapping

```typescript
const STATUS_COLORS: Record<string, { variant: string; className?: string }> = {
  planning: { variant: "secondary" },
  in_progress: { variant: "default" },        // primary color (teal)
  completed: { variant: "default", className: "bg-green-600" },
  paused: { variant: "outline" },
  archived: { variant: "secondary", className: "opacity-60" },
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Mapbox GL JS | MapLibre GL JS | 2020+ (post-license change) | MapLibre is MIT-licensed, free, no API key; drop-in replacement for Mapbox GL |
| react-map-gl (Mapbox) | react-map-gl/maplibre or maplibre-gl direct | 2021+ | Same API, different backend; for small maps, direct maplibre-gl is simpler than React wrapper |
| shadcn Command+Popover Combobox | shadcn native Combobox (Base UI only) | 2025 | Native Combobox only works with Base UI; Radix projects still use Command+Popover pattern |
| Individual @radix-ui/* packages | Unified radix-ui package | 2025 | This project already uses `radix-ui: ^1.4.3` (unified) |

**Deprecated/outdated:**
- Mapbox GL JS free tier: No longer available for new projects without token; use MapLibre GL JS instead
- shadcn Toast component: Replaced by Sonner (already migrated in Phase 2)

## Open Questions

1. **WebGL Context Limits for Card Grid**
   - What we know: Browsers limit WebGL contexts to ~8-16 simultaneous. Each MapLibre map instance is one context.
   - What's unclear: Exact behavior when the card grid has 20+ projects. Will maps auto-recover when scrolled into view? Or do we need explicit Intersection Observer management?
   - Recommendation: Start with lazy-loading via Intersection Observer. If performance issues persist, fall back to rendering static images server-side and only use MapLibre on the detail page. Test with 10-20 cards in development to validate.
   - **Confidence:** MEDIUM -- WebGL limit is known; exact MapLibre behavior at scale needs testing

2. **User List Endpoint for Assignment Combobox**
   - What we know: The existing `/users` endpoint requires admin role. Project managers (including project-level managers) also need to assign members but may not be admins.
   - What's unclear: Whether to create a new lightweight endpoint (e.g., `/users/assignable`) that returns only `id`, `displayName`, `email` without requiring admin role, or to pass the user list from a server-side fetch.
   - Recommendation: Create a new `GET /projects/{id}/assignable-users` endpoint that checks the caller is admin OR project manager for that project. Returns a minimal user list (id, display_name, email) for the combobox. This keeps permission logic server-side.
   - **Confidence:** MEDIUM -- need to decide on endpoint design during planning

3. **OSM Tile Usage Policy for Production**
   - What we know: OpenStreetMap tile servers have a usage policy (max ~250k tiles/day, must include attribution, no heavy use).
   - What's unclear: Whether the production deployment (internal tool, ~5-20 users) will exceed these limits.
   - Recommendation: For an internal tool with 5-20 concurrent users, OSM tiles are fine. Each card mini-map loads ~4-6 tiles. 20 cards x 6 tiles x 20 users = 2,400 tiles/day -- well within policy. Add attribution. If scaling, self-host with tileserver-gl.
   - **Confidence:** HIGH -- usage calculation shows well within limits

4. **Status Column Migration for Existing Projects**
   - What we know: The `projects` table exists and may have data. Adding a `status` column with `DEFAULT 'planning'` sets existing rows to 'planning'.
   - What's unclear: Whether existing projects in the production database have different actual statuses that should be preserved.
   - Recommendation: Use `ALTER TABLE ADD COLUMN ... DEFAULT 'planning'` for the migration. Existing projects get 'planning' status which can be manually corrected. Also update `init.sql` for fresh deployments.
   - **Confidence:** HIGH -- standard SQL migration pattern

## Sources

### Primary (HIGH confidence)
- Existing codebase analysis: `/home/rosen/fiberq/server/db/init.sql` -- full schema with `projects` table, `bounds_geom` column, all `project_id` foreign keys
- Existing codebase analysis: `/home/rosen/fiberq/server/api/projects/routes.py` -- current project CRUD endpoints
- Existing codebase analysis: `/home/rosen/fiberq/web/src/app/[locale]/users/` -- Phase 2 patterns (Server Components, Server Actions, client wrappers, dialogs)
- PostGIS ST_Extent: https://postgis.net/docs/ST_Extent.html -- aggregate bounding box function
- PostGIS ST_Envelope: https://postgis.net/docs/ST_Envelope.html -- geometry to bounding box
- MapLibre GL JS docs: https://maplibre.org/maplibre-gl-js/docs/ -- non-interactive map, fitBounds, GeoJSON source
- MapLibre demotiles: https://github.com/maplibre/demotiles -- free tiles, no API key
- shadcn/ui Combobox (Radix): https://v3.shadcn.com/docs/components/combobox -- Command + Popover pattern

### Secondary (MEDIUM confidence)
- OpenStreetMap tile usage policy: https://wiki.openstreetmap.org/wiki/Tile_servers -- free raster tiles
- WebGL context limits: Known browser behavior, varies by browser/hardware (Chrome ~16, Firefox ~16, Safari ~8)
- react-map-gl/maplibre: https://visgl.github.io/react-map-gl/ -- React wrapper option (not recommended for this use case)

### Tertiary (LOW confidence)
- shadcn/ui Base UI Combobox status: https://github.com/shadcn-ui/ui/issues/9393 -- Radix variant missing, confirmed via GitHub issue

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all core libraries already installed; only maplibre-gl and cmdk are new
- Architecture (backend): HIGH -- extends existing project routes with standard CRUD patterns; PostGIS functions are well-documented
- Architecture (frontend): HIGH -- follows established Phase 2 patterns (Server Components, Server Actions, shadcn/ui)
- Mini-map integration: MEDIUM -- MapLibre GL JS is well-documented but WebGL context limits at scale need testing
- PostGIS extent queries: HIGH -- standard PostGIS aggregate functions, verified from official docs
- Combobox pattern: HIGH -- Command + Popover is the documented Radix approach for shadcn/ui

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (30 days -- stable technologies, no fast-moving concerns)

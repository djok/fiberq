# Phase 4: Dashboard & Analytics - Research

**Researched:** 2026-02-22
**Domain:** Server-side SQL aggregation, stat tile UI, vertical timeline activity feed, next-intl relative time formatting, enriching existing Next.js Server Component page
**Confidence:** HIGH (all data sources exist in DB, no new dependencies needed, patterns well-established from Phase 3)

## Summary

Phase 4 enriches the existing project detail page (`/[locale]/projects/[id]/page.tsx`) with two new sections: stat tiles showing infrastructure counts/metrics and a vertical timeline activity feed. No new pages are created -- only the existing detail page is modified. The critical insight is that all data already exists in the database: element counts come from `ftth_mufovi`, `ftth_stubovi`, `ftth_kablovi_podzemni`, `ftth_kablovi_nadzemni` tables; team size comes from `project_users`; last sync comes from `sync_log`; and activity events come from `sync_log` (uploads), `project_users` (assignments), and `projects._modified_at` (status changes).

The backend work is focused on two new API endpoints: one for project stats (element counts + last sync + team size) and one for the activity feed (paginated, reverse chronological, combining data from multiple tables via UNION ALL). The `_INFRA_TABLES` pattern from the existing `projects/routes.py` can be extended for count queries. For the activity feed, there is no dedicated audit log table -- the feed must be assembled from `sync_log`, `project_users`, and a new lightweight mechanism to track project status changes (since `projects._modified_at` only tracks the most recent modification, not a history).

The frontend work uses existing shadcn/ui Card components for stat tiles with lucide-react icons, and a custom-styled vertical timeline using Tailwind CSS (no external timeline library needed). The `useFormatter` hook from next-intl handles relative time formatting for the "last sync" display with tooltip for exact date. The page remains a Server Component with client-interactive sub-components only where needed (the "Load more" button on the activity feed).

**Primary recommendation:** Add two new API endpoints (`GET /projects/{id}/stats` and `GET /projects/{id}/activity`) and create a `project_activity_log` table for tracking status changes. Enrich the existing project detail page with stat tiles above the map card and an activity feed in the left column below project info.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Stat tiles -- each metric in a separate card with icon and large number (admin dashboard style)
- Metrics: closures, poles, cables, total cable length, team size, last sync
- Totals + delta: shows current total count with small change indicator vs previous sync (if available)
- Last sync shows relative time as main text ("2 hours ago"), exact date on hover/tooltip
- Vertical timeline with icons by action type (visually rich)
- Action types (DASH-02 only): sync uploads, user assignments, status changes
- Initially 20 records + "Load more" button for older entries
- Records grouped by day ("Today", "Yesterday", "20 Feb 2026")
- Stat tiles show em-dash when no data -- not "0"
- Last sync without data: em-dash (consistent with other tiles)
- Activity feed without records: illustration/icon + friendly text message
- New project without any data: normal page with dashes and empty feed (no special banner)

### Claude's Discretion
- Layout integration: how to embed stats and feed in the existing detail page (sections, tabs, ordering)
- Position of stat tiles relative to the map and members
- Whether the feed is always visible or collapsible
- Claude may reorder existing sections from Phase 3 for better UX
- Design of timeline icons and styles

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core (already installed -- no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | Server Components for data fetching, Server Actions for load-more | Already in project |
| React | 19.2.3 | UI rendering | Already in project |
| shadcn/ui (Radix) | Card, Tooltip, ScrollArea, Badge, Skeleton | Stat tiles, tooltip for exact date, feed container | Already in project |
| lucide-react | 0.575.0 | Icons for stat tiles and timeline events | Already in project |
| next-intl | 4.8.3 | Relative time formatting (useFormatter), day grouping, i18n messages | Already in project |
| Tailwind CSS | 4.x | Timeline line, icon circles, responsive grid | Already in project |
| FastAPI + asyncpg | existing | New API endpoints for stats and activity | Already in project |

### Supporting (already available)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Tooltip (Radix) | via radix-ui | Exact date on hover for "last sync" tile | Last sync stat tile |
| Skeleton | shadcn/ui | Loading states for stat tiles and feed | While data loads |
| ScrollArea (Radix) | via radix-ui | Scrollable activity feed if it grows long | Activity feed container |

### No New Dependencies Required
This phase uses only libraries already installed. The timeline is built with Tailwind CSS classes (vertical line, positioned circles). No external timeline, chart, or animation libraries are needed.

**Installation:**
```bash
# No new packages to install
```

## Architecture Patterns

### Recommended Changes to Existing Structure
```
web/src/
├── app/[locale]/projects/
│   ├── [id]/page.tsx            # MODIFY: add stats + activity data fetching, restructure layout
│   ├── _actions.ts              # MODIFY: add fetchActivity server action for "load more"
│   └── _components/
│       ├── project-stats.tsx        # NEW: stat tiles grid (server component)
│       ├── project-activity.tsx     # NEW: activity feed with load-more (client component)
│       ├── activity-timeline.tsx    # NEW: pure timeline rendering (presentational)
│       └── stat-tile.tsx            # NEW: individual stat card (presentational)
server/api/
├── projects/
│   ├── routes.py                # MODIFY: add /stats and /activity endpoints
│   └── models.py               # MODIFY: add ProjectStats and ActivityEntry models
└── db/
    └── init.sql                 # MODIFY: add project_activity_log table
```

### Pattern 1: Server Component Data Aggregation
**What:** The project detail page is an async Server Component. Stat data is fetched server-side and rendered directly -- no client-side fetching or useEffect needed.
**When to use:** For data that loads with the page (stat tiles, initial activity feed batch).
**Example:**
```typescript
// In [id]/page.tsx (Server Component)
import { apiFetch } from "@/lib/api";

// Fetch stats alongside existing project data
const [project, stats, initialActivity] = await Promise.all([
  apiFetch<ApiProjectDetail>(`/projects/${id}`),
  apiFetch<ApiProjectStats>(`/projects/${id}/stats`),
  apiFetch<ApiActivityPage>(`/projects/${id}/activity?limit=20`),
]);
```

### Pattern 2: Server Action for Cursor-Based Pagination
**What:** "Load more" button triggers a Server Action that fetches older activity entries using cursor-based pagination (timestamp of oldest visible entry as cursor).
**When to use:** Activity feed "Load more" button.
**Example:**
```typescript
// In _actions.ts
"use server";

export async function fetchActivity(
  projectId: number,
  before?: string, // ISO timestamp cursor
): Promise<ActionResult<ActivityPage>> {
  const url = before
    ? `/projects/${projectId}/activity?limit=20&before=${before}`
    : `/projects/${projectId}/activity?limit=20`;
  const data = await apiFetch<ApiActivityPage>(url);
  // map snake_case to camelCase
  return { success: true, data: mapActivityPage(data) };
}
```

### Pattern 3: Stat Tile with Empty State
**What:** Each stat tile renders an icon, label, large number (or em-dash for no data), and optional delta indicator.
**When to use:** All 6 stat metrics.
**Example:**
```typescript
// stat-tile.tsx
interface StatTileProps {
  icon: React.ReactNode;
  label: string;
  value: number | null;
  delta?: number | null;
  formatValue?: (v: number) => string;
}

function StatTile({ icon, label, value, delta, formatValue }: StatTileProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          {icon}
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold">
            {value !== null ? (formatValue ? formatValue(value) : value) : "\u2014"}
          </p>
          {delta !== null && delta !== undefined && delta !== 0 && (
            <p className={cn("text-xs", delta > 0 ? "text-green-600" : "text-red-600")}>
              {delta > 0 ? "+" : ""}{delta}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Pattern 4: Vertical Timeline with Day Grouping
**What:** Activity entries rendered as a vertical timeline with a continuous left-side line, colored icon circles by event type, and day group headers.
**When to use:** Activity feed section.
**Example:**
```typescript
// Tailwind-based timeline structure
<div className="relative">
  {/* Vertical line */}
  <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

  {/* Day group header */}
  <div className="relative flex items-center gap-3 pb-2">
    <div className="z-10 flex size-8 items-center justify-center rounded-full bg-background border">
      <CalendarDays className="size-4 text-muted-foreground" />
    </div>
    <span className="text-sm font-medium text-muted-foreground">Today</span>
  </div>

  {/* Timeline entry */}
  <div className="relative flex gap-3 pb-4 pl-0">
    <div className="z-10 flex size-8 shrink-0 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
      <Upload className="size-4 text-blue-600 dark:text-blue-400" />
    </div>
    <div className="min-w-0 flex-1 pt-0.5">
      <p className="text-sm">User uploaded 42 features</p>
      <p className="text-xs text-muted-foreground">14:30</p>
    </div>
  </div>
</div>
```

### Pattern 5: Relative Time with Tooltip (for Last Sync tile)
**What:** The "last sync" stat tile shows relative time as the main text with exact date visible on hover via Radix Tooltip. Since the stat tiles are rendered by a Server Component, use `getFormatter`/`getNow` from `next-intl/server` for the initial render. A small client wrapper can handle tooltip interactivity.
**When to use:** Last sync stat tile only.
**Example:**
```typescript
// Server-side relative time (in Server Component)
import { getFormatter, getNow } from "next-intl/server";

const format = await getFormatter();
const now = await getNow();
const relativeText = lastSyncAt
  ? format.relativeTime(new Date(lastSyncAt), now)
  : null;

// Pass relativeText and exactDate as props to client Tooltip wrapper
```

### Recommended Layout Integration (Claude's Discretion)

Restructure the existing 3-column grid layout of the project detail page:

```
+--------------------------------------------------+
| [<- Back]   Project Name   [Status Badge]        |
+--------------------------------------------------+
| Stat Tiles (3x2 grid spanning full width)        |
| [Closures] [Poles] [Cables]                      |
| [Cable Len] [Team] [Last Sync]                   |
+--------------------------------------------------+
| Left Column (2/3)        | Right Column (1/3)    |
| [Map Card]               | [Members Card]        |
| [Activity Feed]          | [Actions Card]        |
+--------------------------------------------------+
```

Rationale:
- Stat tiles at top: first thing user sees, provides instant project health overview
- Stats span full width for visual impact (admin dashboard style per user decision)
- Map remains prominent in left column
- Activity feed below map in left column (naturally reads top-to-bottom)
- Members and actions stay in right column (interactive sidebar pattern from Phase 3)
- Feed is always visible (not collapsible) -- collapsing adds complexity without clear benefit for a detail page users navigate to intentionally

### Anti-Patterns to Avoid
- **Client-side data fetching for initial stats:** Stats should be fetched server-side with the page, not via useEffect. This ensures fast initial paint and avoids loading spinners.
- **Separate API calls per stat tile:** Fetch all stats in a single API call, not 6 separate requests.
- **Building a full audit system:** This phase only needs to READ existing data + track status changes. Don't build a generic audit framework.
- **Real-time updates with WebSocket:** The feed refreshes on page load. Real-time is out of scope.
- **Custom chart library for deltas:** Deltas are simple "+N" text, not charts. Don't add chart dependencies.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative time formatting | Custom "X ago" function | `next-intl` `getFormatter().relativeTime()` / `useFormatter().relativeTime()` | Handles locale-aware formatting, proper pluralization in BG/EN |
| Day grouping ("Today", "Yesterday", date) | Manual date comparison | `next-intl` `getFormatter().dateTime()` with `Intl.DateTimeFormat` for day labels | Locale-aware day names and date formatting |
| Tooltip component | Custom hover popup | Radix Tooltip (already in `components/ui/tooltip.tsx`) | Accessible, positioned correctly, keyboard support |
| Loading skeleton | Custom shimmer animation | shadcn/ui Skeleton (already in `components/ui/skeleton.tsx`) | Consistent with rest of app |
| Cursor-based pagination | Offset-based pagination | Timestamp cursor (`before` parameter) | More reliable with concurrent inserts, no skipped/duplicated entries |

**Key insight:** This phase is primarily a data aggregation and presentation task. The database tables already contain all the data -- the work is writing SQL queries and rendering the results attractively.

## Common Pitfalls

### Pitfall 1: N+1 Queries for Element Counts
**What goes wrong:** Querying each infrastructure table separately results in 5+ sequential database queries for counts alone.
**Why it happens:** Natural instinct to query `SELECT COUNT(*) FROM ftth_mufovi WHERE project_id = $1`, then `SELECT COUNT(*) FROM ftth_stubovi WHERE project_id = $1`, etc.
**How to avoid:** Use a single query with UNION ALL + GROUP BY, or lateral joins, to get all counts in one round-trip:
```sql
SELECT
  SUM(CASE WHEN source = 'mufovi' THEN cnt ELSE 0 END) as closures,
  SUM(CASE WHEN source = 'stubovi' THEN cnt ELSE 0 END) as poles,
  SUM(CASE WHEN source IN ('kablovi_podzemni', 'kablovi_nadzemni') THEN cnt ELSE 0 END) as cables,
  SUM(CASE WHEN source IN ('kablovi_podzemni', 'kablovi_nadzemni') THEN total_len ELSE 0 END) as cable_length_m
FROM (
  SELECT 'mufovi' as source, COUNT(*) as cnt, 0 as total_len FROM ftth_mufovi WHERE project_id = $1
  UNION ALL
  SELECT 'stubovi', COUNT(*), 0 FROM ftth_stubovi WHERE project_id = $1
  UNION ALL
  SELECT 'kablovi_podzemni', COUNT(*), COALESCE(SUM(total_len_m), 0) FROM ftth_kablovi_podzemni WHERE project_id = $1
  UNION ALL
  SELECT 'kablovi_nadzemni', COUNT(*), COALESCE(SUM(total_len_m), 0) FROM ftth_kablovi_nadzemni WHERE project_id = $1
) counts;
```
**Warning signs:** Multiple sequential `await pool.fetchrow` calls for counts.

### Pitfall 2: No History for Status Changes
**What goes wrong:** The `projects` table only has `_modified_at` and `_modified_by_sub` -- it does NOT track what changed. You cannot reconstruct a "status changed from X to Y" event from the current schema.
**Why it happens:** The schema was designed for last-modified tracking, not change history.
**How to avoid:** Create a lightweight `project_activity_log` table that records status changes (and optionally member assignments) as they happen. Insert into this table in the existing `update_project` and `assign_member`/`remove_member` API endpoints.
**Warning signs:** Trying to use `_modified_at` as an activity timestamp without knowing what the modification was.

### Pitfall 3: Activity Feed UNION Ordering
**What goes wrong:** When UNION-ing events from `sync_log`, `project_users`, and `project_activity_log`, the timestamp columns have different names (`started_at`, `assigned_at`, `created_at`) and the ordering requires careful aliasing.
**Why it happens:** Different tables use different column names for timestamps.
**How to avoid:** Alias all timestamps to a common name (`event_at`) in the UNION ALL query and ORDER BY the alias. Use cursor-based pagination with this aliased timestamp.
**Warning signs:** Events appearing out of order or missing when paginating.

### Pitfall 4: Delta Calculation Complexity
**What goes wrong:** Computing deltas ("change since last sync") requires knowing the counts at the time of the previous sync, which are not stored anywhere.
**Why it happens:** Sync operations merge features but don't snapshot counts before/after.
**How to avoid:** Two options:
1. **Simple approach:** Use `features_uploaded` from `sync_log` as a proxy for the delta on the most recent sync (shows how many features were added in last sync, not per-element-type deltas)
2. **Accurate approach:** Store element counts in `sync_log.details` JSONB during each sync operation
Recommend option 1 for Phase 4 -- it's available now without schema changes to the sync flow. Show a single aggregate delta from the last sync, not per-metric deltas.
**Warning signs:** Trying to compute exact per-metric deltas without historical count snapshots.

### Pitfall 5: Empty State Confusion Between "0" and "No Data"
**What goes wrong:** Displaying "0 closures" when a project has no closures vs displaying em-dash when data hasn't been synced yet.
**Why it happens:** Both cases return 0 from a COUNT query.
**How to avoid:** If ANY infrastructure data exists for the project (at least one row in any `ftth_*` table), show counts (including 0). If NO infrastructure data exists at all, show em-dashes. Check this with a single existence query: `SELECT EXISTS(SELECT 1 FROM (UNION ALL of all infra tables) WHERE project_id = $1)`.
**Warning signs:** New projects with some closures but no poles showing em-dash for poles.

**Revised approach (simpler):** Actually, per the user decision, em-dash means "no data" -- and for counts, 0 IS meaningful data (project has been synced but has no closures). The em-dash should only appear when the query returns NULL (no rows at all from that table). A `COUNT(*)` never returns NULL, it returns 0. So the API should distinguish between "project has infrastructure data" (return counts including 0) vs "project has no infrastructure data" (return null values). The simplest approach: if there's at least one sync_log entry for the project, return actual counts; otherwise return null for all count metrics.

### Pitfall 6: Hydration Mismatch with Relative Time
**What goes wrong:** Server renders "2 hours ago" but by the time client hydrates, it's "2 hours and 1 second ago", causing a React hydration error.
**Why it happens:** Relative time changes between server render and client hydration.
**How to avoid:** Render relative time only in Server Components (no hydration issue). If client-side re-rendering is needed (for live updates), use `useNow` with `updateInterval` from next-intl. For this phase, server-rendered relative time is sufficient -- the page refreshes on navigation.
**Warning signs:** Console hydration mismatch warnings in development.

## Code Examples

Verified patterns from the existing codebase and official documentation:

### Backend: Stats Endpoint SQL Query
```python
# Source: Extending existing _INFRA_TABLES pattern from projects/routes.py

async def _get_project_stats(project_id: int, pool) -> dict:
    """Fetch all project stats in minimal DB round-trips."""

    # 1. Element counts (single query via UNION ALL)
    counts_row = await pool.fetchrow("""
        SELECT
            SUM(CASE WHEN source = 'mufovi' THEN cnt ELSE 0 END) as closures,
            SUM(CASE WHEN source = 'stubovi' THEN cnt ELSE 0 END) as poles,
            SUM(CASE WHEN source IN ('kp', 'kn') THEN cnt ELSE 0 END) as cables,
            SUM(CASE WHEN source IN ('kp', 'kn') THEN total_len ELSE 0 END) as cable_length_m,
            SUM(cnt) as total_elements
        FROM (
            SELECT 'mufovi' as source, COUNT(*) as cnt, 0::real as total_len
                FROM ftth_mufovi WHERE project_id = $1
            UNION ALL
            SELECT 'stubovi', COUNT(*), 0
                FROM ftth_stubovi WHERE project_id = $1
            UNION ALL
            SELECT 'kp', COUNT(*), COALESCE(SUM(total_len_m), 0)
                FROM ftth_kablovi_podzemni WHERE project_id = $1
            UNION ALL
            SELECT 'kn', COUNT(*), COALESCE(SUM(total_len_m), 0)
                FROM ftth_kablovi_nadzemni WHERE project_id = $1
        ) counts
    """, project_id)

    # 2. Team size (single query)
    team_row = await pool.fetchrow(
        "SELECT COUNT(*) as team_size FROM project_users WHERE project_id = $1",
        project_id
    )

    # 3. Last sync (single query)
    sync_row = await pool.fetchrow("""
        SELECT completed_at, features_uploaded
        FROM sync_log
        WHERE project_id = $1 AND status = 'completed'
        ORDER BY completed_at DESC
        LIMIT 1
    """, project_id)

    has_data = counts_row["total_elements"] > 0 if counts_row else False

    return {
        "closures": counts_row["closures"] if has_data else None,
        "poles": counts_row["poles"] if has_data else None,
        "cables": counts_row["cables"] if has_data else None,
        "cable_length_m": round(counts_row["cable_length_m"], 1) if has_data else None,
        "team_size": team_row["team_size"],
        "last_sync_at": sync_row["completed_at"] if sync_row else None,
        "last_sync_features": sync_row["features_uploaded"] if sync_row else None,
    }
```

### Backend: Activity Feed UNION Query
```python
# Source: Pattern based on existing sync/routes.py and projects/routes.py

async def _get_project_activity(
    project_id: int, pool, limit: int = 20, before: str | None = None
) -> list[dict]:
    """Fetch activity feed combining sync_log, project_users, and activity_log."""

    before_clause = "AND event_at < $2" if before else ""
    params = [project_id]
    if before:
        params.append(before)

    query = f"""
        SELECT event_type, event_at, user_sub, user_display_name, details
        FROM (
            -- Sync uploads
            SELECT
                'sync_upload' as event_type,
                COALESCE(sl.completed_at, sl.started_at) as event_at,
                sl.user_sub,
                ul.username as user_display_name,
                jsonb_build_object(
                    'features_uploaded', sl.features_uploaded,
                    'sync_type', sl.sync_type
                ) as details
            FROM sync_log sl
            LEFT JOIN user_logins ul ON ul.user_sub = sl.user_sub
            WHERE sl.project_id = $1 AND sl.status = 'completed'

            UNION ALL

            -- User assignments
            SELECT
                'member_assigned' as event_type,
                pu.assigned_at as event_at,
                pu.assigned_by_sub as user_sub,
                pu.user_display_name,
                jsonb_build_object(
                    'member_name', pu.user_display_name,
                    'project_role', pu.project_role
                ) as details
            FROM project_users pu
            WHERE pu.project_id = $1

            UNION ALL

            -- Status changes (from activity_log table)
            SELECT
                'status_change' as event_type,
                pal.created_at as event_at,
                pal.user_sub,
                ul.username as user_display_name,
                pal.details
            FROM project_activity_log pal
            LEFT JOIN user_logins ul ON ul.user_sub = pal.user_sub
            WHERE pal.project_id = $1 AND pal.event_type = 'status_change'
        ) combined
        WHERE TRUE {before_clause}
        ORDER BY event_at DESC
        LIMIT {limit + 1}
    """
    # Fetch limit+1 to know if there are more entries
    rows = await pool.fetch(query, *params)
    has_more = len(rows) > limit
    entries = [dict(r) for r in rows[:limit]]
    return {"entries": entries, "has_more": has_more}
```

### Backend: project_activity_log Table
```sql
-- Lightweight activity log for events that need explicit tracking
-- (status changes are not captured by existing tables)
CREATE TABLE IF NOT EXISTS project_activity_log (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- 'status_change', 'member_removed'
    user_sub TEXT NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pal_project ON project_activity_log (project_id, created_at DESC);
```

### Frontend: Server Component Page Structure
```typescript
// Source: Extending existing [id]/page.tsx pattern

// Fetch all data in parallel (Server Component)
const [projectData, statsData, activityData] = await Promise.all([
  apiFetch<ApiProjectDetail>(`/projects/${id}`),
  apiFetch<ApiProjectStats>(`/projects/${id}/stats`),
  apiFetch<ApiActivityPage>(`/projects/${id}/activity?limit=20`),
]);

const project = mapProjectDetail(projectData);
const stats = mapStats(statsData);
const activity = mapActivityPage(activityData);

// Render:
// 1. Header (existing)
// 2. Stat tiles grid (NEW - server component, no interactivity)
// 3. Left/Right column layout
//    - Left: Map + Activity Feed
//    - Right: Members + Actions (existing)
```

### Frontend: Relative Time with Tooltip
```typescript
// Source: next-intl docs (https://next-intl.dev/docs/usage/dates-times)
// For Server Component rendering:
import { getFormatter, getNow } from "next-intl/server";

// In the page component:
const format = await getFormatter();
const now = await getNow();
const lastSyncRelative = stats.lastSyncAt
  ? format.relativeTime(new Date(stats.lastSyncAt), now)
  : null;
const lastSyncExact = stats.lastSyncAt
  ? format.dateTime(new Date(stats.lastSyncAt), {
      dateStyle: "medium",
      timeStyle: "short",
    })
  : null;

// Pass to StatTile with tooltip:
<Tooltip>
  <TooltipTrigger asChild>
    <span className="text-2xl font-bold cursor-default">{lastSyncRelative}</span>
  </TooltipTrigger>
  <TooltipContent>{lastSyncExact}</TooltipContent>
</Tooltip>
```

### Frontend: Day Grouping Utility
```typescript
// Group activity entries by day for timeline rendering
type DayGroup = {
  label: string;  // "Today", "Yesterday", or formatted date
  entries: ActivityEntry[];
};

function groupByDay(entries: ActivityEntry[], locale: string): DayGroup[] {
  const groups: Map<string, ActivityEntry[]> = new Map();

  for (const entry of entries) {
    const dateKey = new Date(entry.eventAt).toDateString();
    if (!groups.has(dateKey)) {
      groups.set(dateKey, []);
    }
    groups.get(dateKey)!.push(entry);
  }

  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  return Array.from(groups.entries()).map(([dateKey, dayEntries]) => ({
    label: dateKey === today
      ? t("today")
      : dateKey === yesterday
        ? t("yesterday")
        : new Date(dateKey).toLocaleDateString(locale, {
            day: "numeric",
            month: "short",
            year: "numeric",
          }),
    entries: dayEntries,
  }));
}
```

### Lucide Icons by Event Type
```typescript
// Source: lucide.dev/icons/
import {
  Upload, UserPlus, RefreshCw, ArrowRightLeft,
  Box, Zap, Cable, Ruler, Users, Clock,
  TrendingUp, TrendingDown, Minus,
} from "lucide-react";

// Stat tile icons
const STAT_ICONS = {
  closures: <Box className="size-5" />,
  poles: <Zap className="size-5" />,
  cables: <Cable className="size-5" />,
  cableLength: <Ruler className="size-5" />,
  teamSize: <Users className="size-5" />,
  lastSync: <Clock className="size-5" />,
};

// Activity feed event type icons + colors
const EVENT_ICONS: Record<string, { icon: React.ReactNode; bg: string }> = {
  sync_upload: {
    icon: <Upload className="size-4" />,
    bg: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
  },
  member_assigned: {
    icon: <UserPlus className="size-4" />,
    bg: "bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400",
  },
  status_change: {
    icon: <ArrowRightLeft className="size-4" />,
    bg: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
  },
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Client-side useEffect data fetching | Server Component async data fetching | Next.js 13+ (App Router) | No loading spinners for initial data, faster paint |
| Offset-based pagination (OFFSET N) | Cursor-based pagination (WHERE ts < cursor) | Industry best practice | No skipped/duplicated entries on concurrent writes |
| External timeline components (react-vertical-timeline) | Tailwind CSS custom timeline | 2023+ (Tailwind v3/v4) | No extra dependency, full design control, dark mode support |
| moment.js / date-fns for relative time | Intl.RelativeTimeFormat via next-intl | Built into modern browsers | No dependency, locale-aware, integrated with i18n |

**Deprecated/outdated:**
- `moment.js`: Deprecated, replaced by native Intl APIs
- `react-vertical-timeline-component`: Last updated 2022, not maintained for React 19, unnecessary for simple timelines

## Data Source Analysis

### What data already exists in the database

| Metric / Event | Source Table | Key Columns | Notes |
|----------------|-------------|-------------|-------|
| Closures count | `ftth_mufovi` | `project_id`, `id` | COUNT(*) WHERE project_id = $1 |
| Poles count | `ftth_stubovi` | `project_id`, `id` | COUNT(*) WHERE project_id = $1 |
| Cables count | `ftth_kablovi_podzemni` + `ftth_kablovi_nadzemni` | `project_id`, `id` | SUM of both tables |
| Cable total length | `ftth_kablovi_podzemni` + `ftth_kablovi_nadzemni` | `total_len_m` | SUM(total_len_m) from both tables |
| Team size | `project_users` | `project_id` | COUNT(*) WHERE project_id = $1 |
| Last sync | `sync_log` | `project_id`, `completed_at`, `status` | Most recent completed entry |
| Sync uploads (feed) | `sync_log` | `project_id`, `user_sub`, `features_uploaded`, `completed_at` | WHERE sync_type = 'upload' AND status = 'completed' |
| Member assignments (feed) | `project_users` | `project_id`, `assigned_at`, `assigned_by_sub`, `user_display_name` | All rows for project |
| Status changes (feed) | **DOES NOT EXIST** | -- | Needs new `project_activity_log` table |

### What needs to be created

1. **`project_activity_log` table** -- Records status changes and member removals (events that aren't captured by existing tables). Lightweight: just `project_id`, `event_type`, `user_sub`, `details` (JSONB), `created_at`.

2. **Insert triggers in existing endpoints** -- When `update_project` changes status, insert a row into `project_activity_log`. When `remove_member` deletes a project_users row, insert a row (since the row is gone, we can't query it later for the feed).

3. **Two new API endpoints:**
   - `GET /projects/{id}/stats` -- Returns all stat metrics in one response
   - `GET /projects/{id}/activity?limit=N&before=ISO_TIMESTAMP` -- Returns paginated activity feed

## Open Questions

1. **Delta calculation granularity**
   - What we know: `sync_log.features_uploaded` tracks total features per sync but not per element type. Computing per-metric deltas (e.g., "+5 closures since last sync") requires either (a) historical count snapshots or (b) diffing current vs post-sync counts.
   - What's unclear: Whether the user expects per-metric deltas or a single aggregate delta.
   - Recommendation: For Phase 4, show the last sync's `features_uploaded` count as the delta on a general level (e.g., on the last sync tile: "+42 features"). Per-metric deltas can be added later if `sync_log.details` JSONB is populated with per-table counts during sync. This avoids schema changes to the sync flow in this phase.

2. **Member removal events in the feed**
   - What we know: When a member is removed, the `project_users` row is deleted (no soft delete). This means the removal event cannot be reconstructed from existing data.
   - What's unclear: Whether the activity feed should show "User X was removed" events.
   - Recommendation: Track removals in `project_activity_log` with details including the removed user's name. The `remove_member` endpoint already has this information.

3. **Existing activity data for demo/testing**
   - What we know: The database may have minimal or no sync_log entries and limited project_users history.
   - What's unclear: Whether seed data is needed for development.
   - Recommendation: The empty state is well-defined (em-dashes and friendly message), so the feature works correctly even with no data. Seed data is nice-to-have but not blocking.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `server/db/init.sql` -- Full database schema with all infrastructure tables, sync_log, project_users
- Existing codebase: `server/api/projects/routes.py` -- Existing UNION ALL pattern for extent queries, permission model
- Existing codebase: `web/src/app/[locale]/projects/[id]/page.tsx` -- Current page structure, data flow pattern
- Existing codebase: `web/src/app/[locale]/projects/_actions.ts` -- Server Action pattern with ActionResult discriminated union
- [next-intl date/time formatting docs](https://next-intl.dev/docs/usage/dates-times) -- `getFormatter().relativeTime()` API for server/client

### Secondary (MEDIUM confidence)
- [Lucide React icons](https://lucide.dev/icons/) -- Icon availability verified (Upload, UserPlus, Cable, Clock, etc.)
- [next-intl relative time with useNow](https://next-intl.dev/docs/usage/dates-times) -- Client-side relative time updating pattern

### Tertiary (LOW confidence)
- None -- all research verified against codebase and official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No new dependencies, all libraries already installed and patterns established in Phase 2-3
- Architecture: HIGH -- Extending existing Server Component + Server Action patterns with well-understood SQL aggregation
- Pitfalls: HIGH -- Data source analysis done against actual schema, edge cases (empty state, no status history) identified from code review
- Activity feed data model: HIGH -- Verified sync_log and project_users schemas, identified gap (status change history) with clear solution

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (stable -- no fast-moving dependencies)

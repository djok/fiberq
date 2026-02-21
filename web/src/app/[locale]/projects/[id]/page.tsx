import {
  setRequestLocale,
  getTranslations,
  getFormatter,
  getNow,
} from "next-intl/server";
import { auth } from "@/auth";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProjectDetailActions } from "../_components/project-detail-actions";
import { ProjectMiniMap } from "../_components/project-mini-map";
import { ProjectStats } from "../_components/project-stats";
import { ProjectActivity } from "../_components/project-activity";
import type {
  ProjectDetail,
  ProjectMember,
  ProjectStats as ProjectStatsType,
  ActivityEntry,
} from "@/types/project";

type ApiProjectMember = {
  id: number;
  user_sub: string;
  user_display_name: string | null;
  user_email: string | null;
  project_role: string;
  assigned_at: string;
};

type ApiProjectDetail = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  created_by_sub: string | null;
  members: ApiProjectMember[];
  extent: GeoJSON.Geometry | null;
};

type ApiProjectStats = {
  closures: number | null;
  poles: number | null;
  cables: number | null;
  cable_length_m: number | null;
  team_size: number;
  last_sync_at: string | null;
  last_sync_features: number | null;
};

type ApiActivityEntry = {
  event_type: string;
  event_at: string;
  user_sub: string | null;
  user_display_name: string | null;
  details: Record<string, unknown> | null;
};

type ApiActivityPage = {
  entries: ApiActivityEntry[];
  has_more: boolean;
};

function mapMember(m: ApiProjectMember): ProjectMember {
  return {
    id: m.id,
    userSub: m.user_sub,
    userDisplayName: m.user_display_name,
    userEmail: m.user_email,
    projectRole: m.project_role,
    assignedAt: m.assigned_at,
  };
}

function mapProjectDetail(p: ApiProjectDetail): ProjectDetail {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    status: p.status,
    createdAt: p.created_at,
    createdBySub: p.created_by_sub,
    members: p.members.map(mapMember),
    extent: p.extent,
  };
}

function mapStats(s: ApiProjectStats): ProjectStatsType {
  return {
    closures: s.closures,
    poles: s.poles,
    cables: s.cables,
    cableLengthM: s.cable_length_m,
    teamSize: s.team_size,
    lastSyncAt: s.last_sync_at,
    lastSyncFeatures: s.last_sync_features,
  };
}

function mapActivityEntries(entries: ApiActivityEntry[]): ActivityEntry[] {
  return entries.map((e) => ({
    eventType: e.event_type,
    eventAt: e.event_at,
    userSub: e.user_sub,
    userDisplayName: e.user_display_name,
    details: e.details,
  }));
}

const STATUS_LABEL_MAP: Record<string, string> = {
  planning: "statusPlanning",
  in_progress: "statusInProgress",
  completed: "statusCompleted",
  paused: "statusPaused",
  archived: "statusArchived",
};

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session) {
    redirect(`/${locale}/api/auth/signin`);
  }

  const t = await getTranslations("projects");
  const td = await getTranslations("dashboard");

  // Fetch project data (required) and stats/activity (optional, graceful fallback)
  let project: ProjectDetail;
  let stats: ProjectStatsType | null = null;
  let activityEntries: ActivityEntry[] = [];
  let activityHasMore = false;

  try {
    const data = await apiFetch<ApiProjectDetail>(`/projects/${id}`);
    project = mapProjectDetail(data);
  } catch {
    notFound();
  }

  // Fetch stats and activity in parallel -- don't block page if they fail
  const [statsResult, activityResult] = await Promise.allSettled([
    apiFetch<ApiProjectStats>(`/projects/${id}/stats`),
    apiFetch<ApiActivityPage>(`/projects/${id}/activity?limit=20`),
  ]);

  if (statsResult.status === "fulfilled") {
    stats = mapStats(statsResult.value);
  }

  if (activityResult.status === "fulfilled") {
    activityEntries = mapActivityEntries(activityResult.value.entries);
    activityHasMore = activityResult.value.has_more;
  }

  // Compute relative time for last sync
  let lastSyncRelative: string | null = null;
  let lastSyncExact: string | null = null;

  if (stats?.lastSyncAt) {
    const format = await getFormatter();
    const now = await getNow();
    lastSyncRelative = format.relativeTime(new Date(stats.lastSyncAt), now);
    lastSyncExact = format.dateTime(new Date(stats.lastSyncAt), {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  // Determine if user can manage this project
  const userRoles = session.user.roles;
  const isAdmin = userRoles.includes("admin");
  const isGlobalPM = userRoles.includes("project_manager");
  const isProjectManager = project.members.some(
    (m) =>
      m.userSub === session.user.id && m.projectRole === "manager",
  );
  const canManage = isAdmin || isGlobalPM || isProjectManager;

  const statsTranslations = {
    closures: td("closures"),
    poles: td("poles"),
    cables: td("cables"),
    cableLength: td("cableLength"),
    teamSize: td("teamSize"),
    lastSync: td("lastSync"),
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/${locale}/projects`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          {t("backToProjects")}
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{project.name}</h1>
        <Badge
          variant={
            project.status === "completed"
              ? "default"
              : project.status === "archived"
                ? "secondary"
                : project.status === "in_progress"
                  ? "default"
                  : project.status === "paused"
                    ? "outline"
                    : "secondary"
          }
        >
          {t(STATUS_LABEL_MAP[project.status] ?? "statusPlanning")}
        </Badge>
      </div>

      {/* Stat Tiles Row - full width */}
      {stats && (
        <ProjectStats
          stats={stats}
          lastSyncRelative={lastSyncRelative}
          lastSyncExact={lastSyncExact}
          translations={statsTranslations}
        />
      )}

      {/* Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Map Card */}
          <Card>
            <CardContent className="p-0 overflow-hidden rounded-lg">
              <ProjectMiniMap
                extent={project.extent}
                interactive
                className="h-[300px] w-full"
              />
            </CardContent>
          </Card>

          {/* Project Info Card (simplified - no duplicate name/status) */}
          <Card>
            <CardHeader>
              <CardTitle>{t("projectInfo")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <p className="text-sm text-muted-foreground">
                    {t("description")}
                  </p>
                  <p className="text-sm mt-1">
                    {project.description || "-"}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t("createdAt")}
                  </p>
                  <p className="text-sm mt-1">
                    {new Date(project.createdAt).toLocaleDateString(locale)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Activity Feed */}
          <ProjectActivity
            projectId={project.id}
            initialEntries={activityEntries}
            initialHasMore={activityHasMore}
            locale={locale}
          />
        </div>

        {/* Right Column - Client component for interactive actions */}
        <div className="space-y-6">
          <ProjectDetailActions
            project={project}
            canManage={canManage}
            locale={locale}
          />
        </div>
      </div>
    </div>
  );
}

import { setRequestLocale, getTranslations } from "next-intl/server";
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
import type { ProjectDetail, ProjectMember } from "@/types/project";

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

  let project: ProjectDetail;
  try {
    const data = await apiFetch<ApiProjectDetail>(`/projects/${id}`);
    project = mapProjectDetail(data);
  } catch {
    notFound();
  }

  // Determine if user can manage this project:
  // admin, global project_manager, or project-level manager
  const userRoles = session.user.roles;
  const isAdmin = userRoles.includes("admin");
  const isGlobalPM = userRoles.includes("project_manager");
  const isProjectManager = project.members.some(
    (m) =>
      m.userSub === session.user.id && m.projectRole === "manager",
  );
  const canManage = isAdmin || isGlobalPM || isProjectManager;

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

          {/* Project Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>{t("projectInfo")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">{t("name")}</p>
                  <p className="text-sm mt-1">{project.name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t("status")}
                  </p>
                  <p className="text-sm mt-1">
                    {t(STATUS_LABEL_MAP[project.status] ?? "statusPlanning")}
                  </p>
                </div>
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

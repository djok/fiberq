import { setRequestLocale } from "next-intl/server";
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { ProjectCard } from "@/types/project";
import { ProjectsClient } from "./_components/projects-client";

type ApiProject = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  member_count: number;
  member_names: string[];
  extent: GeoJSON.Geometry | null;
  created_at: string;
};

function mapProject(p: ApiProject): ProjectCard {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    status: p.status,
    memberCount: p.member_count,
    memberNames: p.member_names,
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
    redirect(`/${locale}/api/auth/signin`);
  }

  const canCreate =
    session.user.roles.includes("admin") ||
    session.user.roles.includes("project_manager");

  let projects: ProjectCard[] = [];
  try {
    const data = await apiFetch<ApiProject[]>("/projects");
    projects = data.map(mapProject);
  } catch {
    // API unavailable -- show empty state
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <ProjectsClient
        projects={projects}
        locale={locale}
        canCreate={canCreate}
      />
    </div>
  );
}

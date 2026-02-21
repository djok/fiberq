"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ProjectCard as ProjectCardType } from "@/types/project";
import { ProjectCard } from "./project-card";
import { CreateProjectDialog } from "./create-project-dialog";

interface ProjectsClientProps {
  projects: ProjectCardType[];
  locale: string;
  canCreate: boolean;
}

const STATUS_OPTIONS = [
  "planning",
  "in_progress",
  "completed",
  "paused",
  "archived",
] as const;

const STATUS_LABEL_MAP: Record<string, string> = {
  planning: "statusPlanning",
  in_progress: "statusInProgress",
  completed: "statusCompleted",
  paused: "statusPaused",
  archived: "statusArchived",
};

export function ProjectsClient({
  projects,
  locale,
  canCreate,
}: ProjectsClientProps) {
  const t = useTranslations("projects");

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [userFilter, setUserFilter] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  const allMemberNames = [
    ...new Set(projects.flatMap((p) => p.memberNames)),
  ].sort();

  const filteredProjects = projects.filter((project) => {
    if (
      searchQuery &&
      !project.name.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    if (statusFilter !== "all" && project.status !== statusFilter) {
      return false;
    }
    if (
      userFilter !== "all" &&
      !project.memberNames.includes(userFilter)
    ) {
      return false;
    }
    return true;
  });

  const hasAnyProjects = projects.length > 0;

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t("title")}</h1>
        {canCreate && (
          <Button size="sm" onClick={() => setShowCreateDialog(true)}>
            <Plus className="size-4" />
            {t("createProject")}
          </Button>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          placeholder={t("searchPlaceholder")}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="sm:max-w-[260px]"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("filterByStatus")}</SelectItem>
            {STATUS_OPTIONS.map((status) => (
              <SelectItem key={status} value={status}>
                {t(STATUS_LABEL_MAP[status])}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={userFilter} onValueChange={setUserFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("filterByUser")}</SelectItem>
            {allMemberNames.map((name) => (
              <SelectItem key={name} value={name}>
                {name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Card grid or empty state */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <ProjectCard key={project.id} project={project} locale={locale} />
          ))}
        </div>
      ) : (
        <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed">
          <p className="text-sm text-muted-foreground">
            {!hasAnyProjects
              ? canCreate
                ? t("emptyStateAdmin")
                : t("emptyState")
              : t("emptyState")}
          </p>
        </div>
      )}

      {/* Create dialog */}
      <CreateProjectDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
      />
    </>
  );
}

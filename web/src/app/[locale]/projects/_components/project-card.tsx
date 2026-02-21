"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Users } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ProjectCard as ProjectCardType } from "@/types/project";
import { ProjectMiniMap } from "./project-mini-map";

interface ProjectCardProps {
  project: ProjectCardType;
  locale: string;
}

function getStatusBadgeProps(status: string) {
  switch (status) {
    case "planning":
      return { variant: "secondary" as const, className: "" };
    case "in_progress":
      return { variant: "default" as const, className: "" };
    case "completed":
      return {
        variant: "default" as const,
        className: "bg-green-600 hover:bg-green-600/90",
      };
    case "paused":
      return { variant: "outline" as const, className: "" };
    case "archived":
      return { variant: "secondary" as const, className: "opacity-60" };
    default:
      return { variant: "secondary" as const, className: "" };
  }
}

const STATUS_LABEL_MAP: Record<string, string> = {
  planning: "statusPlanning",
  in_progress: "statusInProgress",
  completed: "statusCompleted",
  paused: "statusPaused",
  archived: "statusArchived",
};

export function ProjectCard({ project, locale }: ProjectCardProps) {
  const t = useTranslations("projects");
  const badgeProps = getStatusBadgeProps(project.status);
  const statusLabel = STATUS_LABEL_MAP[project.status] || project.status;

  return (
    <Link href={`/${locale}/projects/${project.id}`}>
      <Card className="overflow-hidden transition-colors hover:border-primary/50 py-0 gap-0">
        {/* Mini-map */}
        <ProjectMiniMap
          extent={project.extent}
          className="h-[120px] w-full"
        />

        {/* Card info */}
        <CardContent className="space-y-2 p-4">
          <h3 className="font-medium leading-tight line-clamp-1">
            {project.name}
          </h3>

          <div className="flex items-center justify-between">
            <Badge variant={badgeProps.variant} className={badgeProps.className}>
              {t(statusLabel)}
            </Badge>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Users className="size-3" />
              {t("memberCount", { count: project.memberCount })}
            </span>
          </div>

          {project.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {project.description}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

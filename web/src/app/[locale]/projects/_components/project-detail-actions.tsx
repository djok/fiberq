"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProjectMembers } from "./project-members";
import { EditProjectDialog } from "./edit-project-dialog";
import type { ProjectDetail } from "@/types/project";

interface ProjectDetailActionsProps {
  project: ProjectDetail;
  canManage: boolean;
  locale: string;
}

export function ProjectDetailActions({
  project,
  canManage,
}: ProjectDetailActionsProps) {
  const t = useTranslations("projects");
  const [showEditDialog, setShowEditDialog] = React.useState(false);

  return (
    <>
      {/* Members Card */}
      <ProjectMembers
        members={project.members}
        projectId={project.id}
        canManage={canManage}
      />

      {/* Actions Card */}
      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle>{t("actions")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setShowEditDialog(true)}
            >
              {t("editProject")}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Edit Dialog */}
      <EditProjectDialog
        project={project}
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
      />
    </>
  );
}

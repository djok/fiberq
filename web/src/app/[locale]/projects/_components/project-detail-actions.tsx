"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConfirmActionDialog } from "@/app/[locale]/users/_components/confirm-action-dialog";
import { ProjectMembers } from "./project-members";
import { EditProjectDialog } from "./edit-project-dialog";
import { deleteProject } from "../_actions";
import type { ProjectDetail } from "@/types/project";

interface ProjectDetailActionsProps {
  project: ProjectDetail;
  canManage: boolean;
  locale: string;
}

export function ProjectDetailActions({
  project,
  canManage,
  locale,
}: ProjectDetailActionsProps) {
  const t = useTranslations("projects");
  const router = useRouter();
  const [showEditDialog, setShowEditDialog] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [deleteLoading, setDeleteLoading] = React.useState(false);

  async function handleDeleteProject() {
    setDeleteLoading(true);
    try {
      const result = await deleteProject(project.id);
      if (result.success) {
        toast.success(t("deleteSuccess"));
        router.push(`/${locale}/projects`);
      } else {
        toast.error(t("deleteError"), { description: result.error });
      }
    } finally {
      setDeleteLoading(false);
      setShowDeleteDialog(false);
    }
  }

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
            <Button
              variant="destructive"
              className="w-full"
              onClick={() => setShowDeleteDialog(true)}
            >
              {t("deleteProject")}
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

      {/* Delete Confirmation Dialog */}
      <ConfirmActionDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title={t("confirmDeleteTitle")}
        description={t("confirmDeleteDescription", { name: project.name })}
        confirmLabel={t("deleteProject")}
        onConfirm={handleDeleteProject}
        variant="destructive"
        loading={deleteLoading}
      />
    </>
  );
}

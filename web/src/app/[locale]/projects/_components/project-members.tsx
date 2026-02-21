"use client";

import * as React from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ConfirmActionDialog } from "@/app/[locale]/users/_components/confirm-action-dialog";
import { MemberCombobox } from "./member-combobox";
import { removeMember } from "../_actions";
import type { ProjectMember } from "@/types/project";

interface ProjectMembersProps {
  members: ProjectMember[];
  projectId: number;
  canManage: boolean;
}

const ROLE_BADGE_VARIANT: Record<
  string,
  "default" | "secondary" | "outline"
> = {
  manager: "default",
  specialist: "secondary",
  observer: "outline",
};

const ROLE_LABEL_MAP: Record<string, string> = {
  manager: "roleManager",
  specialist: "roleSpecialist",
  observer: "roleObserver",
};

export function ProjectMembers({
  members,
  projectId,
  canManage,
}: ProjectMembersProps) {
  const t = useTranslations("projects");
  const router = useRouter();
  const [confirmRemove, setConfirmRemove] = React.useState<ProjectMember | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function handleRemove() {
    if (!confirmRemove) return;
    setLoading(true);
    try {
      const result = await removeMember(projectId, confirmRemove.id);
      if (result.success) {
        toast.success(t("removeSuccess"));
        router.refresh();
      } else {
        toast.error(result.error);
      }
    } finally {
      setLoading(false);
      setConfirmRemove(null);
    }
  }

  function getInitials(name: string | null): string {
    if (!name) return "?";
    return name
      .split(" ")
      .map((part) => part[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase();
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>{t("members")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Add member combobox (only if canManage) */}
          {canManage && (
            <MemberCombobox
              projectId={projectId}
              existingMemberSubs={members.map((m) => m.userSub)}
            />
          )}

          {/* Member list */}
          {members.length > 0 ? (
            <ScrollArea className="max-h-[320px]">
              <div className="space-y-3">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3"
                  >
                    {/* Avatar placeholder */}
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {getInitials(member.userDisplayName)}
                    </div>

                    {/* Info */}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {member.userDisplayName || member.userSub}
                      </p>
                      {member.userEmail && (
                        <p className="text-xs text-muted-foreground truncate">
                          {member.userEmail}
                        </p>
                      )}
                    </div>

                    {/* Role badge */}
                    <Badge
                      variant={
                        ROLE_BADGE_VARIANT[member.projectRole] ?? "secondary"
                      }
                    >
                      {t(ROLE_LABEL_MAP[member.projectRole] ?? "roleSpecialist")}
                    </Badge>

                    {/* Remove button */}
                    {canManage && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-7 shrink-0"
                        onClick={() => setConfirmRemove(member)}
                      >
                        <X className="size-3.5" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <p className="text-sm text-muted-foreground">
              {t("memberCount", { count: 0 })}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Confirm remove dialog */}
      <ConfirmActionDialog
        open={confirmRemove !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmRemove(null);
        }}
        title={t("removeMember")}
        description={t("removeMemberConfirm")}
        confirmLabel={t("removeMember")}
        onConfirm={handleRemove}
        variant="destructive"
        loading={loading}
      />
    </>
  );
}

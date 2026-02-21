"use client";

import * as React from "react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { ConfirmActionDialog } from "./confirm-action-dialog";
import { ResetTokenDialog } from "./reset-token-dialog";
import { EditRolesDialog } from "./edit-roles-dialog";
import {
  deactivateUser,
  reactivateUser,
  resetUserPassword,
} from "../_actions";
import type { UserRow } from "@/types/user";
import type { CredentialResetResponse } from "@/types/user";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface UserDetailActionsProps {
  user: UserRow;
  locale: string;
}

export function UserDetailActions({ user, locale }: UserDetailActionsProps) {
  const t = useTranslations("users");
  const tRoles = useTranslations("roles");

  const [confirmAction, setConfirmAction] = React.useState<
    "deactivate" | "reactivate" | "reset" | null
  >(null);
  const [resetToken, setResetToken] =
    React.useState<CredentialResetResponse | null>(null);
  const [editRolesOpen, setEditRolesOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  async function handleConfirm() {
    setLoading(true);
    try {
      if (confirmAction === "deactivate") {
        const result = await deactivateUser(user.id);
        if (result.success) {
          toast.success(t("deactivateSuccess"));
        } else {
          toast.error(t("actionError"), { description: result.error });
        }
        setConfirmAction(null);
      } else if (confirmAction === "reactivate") {
        const result = await reactivateUser(user.id);
        if (result.success) {
          toast.success(t("reactivateSuccess"));
        } else {
          toast.error(t("actionError"), { description: result.error });
        }
        setConfirmAction(null);
      } else if (confirmAction === "reset") {
        const result = await resetUserPassword(user.id);
        if (result.success) {
          toast.success(t("resetSuccess"));
          setResetToken(result.data);
        } else {
          toast.error(t("actionError"), { description: result.error });
        }
        setConfirmAction(null);
      }
    } finally {
      setLoading(false);
    }
  }

  function getConfirmTitle() {
    if (confirmAction === "deactivate") return t("confirmDeactivateTitle");
    if (confirmAction === "reactivate") return t("confirmReactivateTitle");
    if (confirmAction === "reset") return t("confirmResetTitle");
    return "";
  }

  function getConfirmDescription() {
    if (confirmAction === "deactivate")
      return t("confirmDeactivateDescription", { name: user.displayName });
    if (confirmAction === "reactivate")
      return t("confirmReactivateDescription", { name: user.displayName });
    if (confirmAction === "reset")
      return t("confirmResetDescription", { name: user.displayName });
    return "";
  }

  function getConfirmLabel() {
    if (confirmAction === "deactivate") return t("deactivate");
    if (confirmAction === "reactivate") return t("reactivate");
    if (confirmAction === "reset") return t("resetPassword");
    return "";
  }

  function getConfirmVariant(): "default" | "destructive" {
    if (confirmAction === "reactivate") return "default";
    return "destructive";
  }

  return (
    <>
      {/* Roles Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("role")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            {user.roles.map((role) => (
              <Badge key={role} variant="secondary">
                {tRoles(role)}
              </Badge>
            ))}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setEditRolesOpen(true)}
          >
            {t("editRoles")}
          </Button>
        </CardContent>
      </Card>

      {/* Actions Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("actions")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {user.isActive ? (
            <Button
              variant="destructive"
              className="w-full"
              onClick={() => setConfirmAction("deactivate")}
            >
              {t("deactivateUser")}
            </Button>
          ) : (
            <Button
              variant="default"
              className="w-full"
              onClick={() => setConfirmAction("reactivate")}
            >
              {t("reactivateUser")}
            </Button>
          )}
          <Button
            variant="outline"
            className="w-full"
            onClick={() => setConfirmAction("reset")}
          >
            {t("resetPassword")}
          </Button>
        </CardContent>
      </Card>

      {/* Projects Placeholder Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("assignedProjects")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {t("projectsPlaceholder")}
          </p>
        </CardContent>
      </Card>

      {/* Account Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t("accountInfo")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm text-muted-foreground">{t("status")}</p>
            <div className="mt-1">
              {user.isActive ? (
                <Badge variant="default">{t("statusActive")}</Badge>
              ) : (
                <Badge variant="destructive">{t("statusInactive")}</Badge>
              )}
            </div>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t("lastLogin")}</p>
            <p className="text-sm mt-1">
              {user.lastLogin
                ? new Date(user.lastLogin).toLocaleString(locale)
                : t("never")}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t("userId")}</p>
            <p className="text-xs text-muted-foreground mt-1 font-mono break-all">
              {user.id}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Dialogs */}
      <ConfirmActionDialog
        open={confirmAction !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmAction(null);
        }}
        title={getConfirmTitle()}
        description={getConfirmDescription()}
        confirmLabel={getConfirmLabel()}
        onConfirm={handleConfirm}
        variant={getConfirmVariant()}
        loading={loading}
      />

      <EditRolesDialog
        open={editRolesOpen}
        onOpenChange={setEditRolesOpen}
        userId={user.id}
        currentRoles={user.roles}
      />

      {resetToken && (
        <ResetTokenDialog
          open={!!resetToken}
          onOpenChange={(open) => {
            if (!open) setResetToken(null);
          }}
          token={resetToken.token}
          resetUrl={resetToken.reset_url}
          ttl={resetToken.ttl}
        />
      )}
    </>
  );
}

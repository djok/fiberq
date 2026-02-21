"use client";

import * as React from "react";
import { MoreHorizontal, Eye, UserX, UserCheck, KeyRound } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { useRouter, usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ConfirmActionDialog } from "./confirm-action-dialog";
import { ResetTokenDialog } from "./reset-token-dialog";
import {
  deactivateUser,
  reactivateUser,
  resetUserPassword,
} from "../_actions";
import type { UserRow } from "@/types/user";
import type { CredentialResetResponse } from "@/types/user";

interface UserActionsProps {
  user: UserRow;
}

export function UserActions({ user }: UserActionsProps) {
  const t = useTranslations("users");
  const router = useRouter();
  const pathname = usePathname();

  const [confirmAction, setConfirmAction] = React.useState<
    "deactivate" | "reactivate" | "reset" | null
  >(null);
  const [resetToken, setResetToken] =
    React.useState<CredentialResetResponse | null>(null);
  const [loading, setLoading] = React.useState(false);

  // Derive locale from pathname (e.g., /en/users -> en)
  const locale = pathname.split("/")[1];

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
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" aria-label={t("actions")}>
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => router.push(`/${locale}/users/${user.id}`)}
          >
            <Eye className="size-4" />
            {t("viewDetails")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          {user.isActive ? (
            <DropdownMenuItem
              variant="destructive"
              onClick={() => setConfirmAction("deactivate")}
            >
              <UserX className="size-4" />
              {t("deactivate")}
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem
              onClick={() => setConfirmAction("reactivate")}
            >
              <UserCheck className="size-4" />
              {t("reactivate")}
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            onClick={() => setConfirmAction("reset")}
          >
            <KeyRound className="size-4" />
            {t("resetPassword")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

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

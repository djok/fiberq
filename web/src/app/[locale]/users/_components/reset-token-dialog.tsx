"use client";

import * as React from "react";
import { Copy, Check } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ResetTokenDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: string;
  resetUrl: string;
  ttl: number;
}

export function ResetTokenDialog({
  open,
  onOpenChange,
  token,
  resetUrl,
  ttl,
}: ResetTokenDialogProps) {
  const t = useTranslations("users");
  const [copied, setCopied] = React.useState(false);

  async function copyToken() {
    await navigator.clipboard.writeText(token);
    setCopied(true);
    toast.success(t("copied"));
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("resetTokenTitle")}</DialogTitle>
          <DialogDescription>{t("resetTokenDescription")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("resetToken")}</label>
            <div className="flex items-center gap-2">
              <code className="flex-1 select-all rounded-md border bg-muted px-3 py-2 font-mono text-lg break-all">
                {token}
              </code>
              <Button
                variant="outline"
                size="icon"
                onClick={copyToken}
                aria-label={t("copyToken")}
              >
                {copied ? (
                  <Check className="size-4" />
                ) : (
                  <Copy className="size-4" />
                )}
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">{t("resetUrl")}</label>
            <a
              href={resetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-md bg-muted px-3 py-2 text-sm text-primary underline break-all"
            >
              {resetUrl}
            </a>
          </div>
          <p className="text-sm text-muted-foreground">
            {t("validFor", { minutes: Math.floor(ttl / 60) })}
          </p>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>{t("close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

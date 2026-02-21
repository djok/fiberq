"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Copy, Check } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { createUser } from "../_actions";
import type { CredentialResetResponse } from "@/types/user";

const ROLES = ["admin", "project_manager", "engineer", "field_worker"] as const;

const createUserSchema = z.object({
  username: z.string().min(2).max(64),
  displayName: z.string().min(1).max(256),
  email: z.string().email(),
  phone: z.string().optional().or(z.literal("")),
  roles: z.array(z.string()).min(1, "At least one role required"),
});

type FormValues = z.infer<typeof createUserSchema>;

export function CreateUserDialog() {
  const t = useTranslations("users");
  const tRoles = useTranslations("roles");

  const [open, setOpen] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [resetData, setResetData] =
    React.useState<CredentialResetResponse | null>(null);
  const [copied, setCopied] = React.useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      username: "",
      displayName: "",
      email: "",
      phone: "",
      roles: [],
    },
  });

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      const result = await createUser({
        username: values.username,
        display_name: values.displayName,
        email: values.email,
        phone: values.phone || undefined,
        roles: values.roles,
      });

      if (result.success) {
        toast.success(t("createSuccess"));
        setResetData(result.data);
      } else {
        toast.error(t("createError"), { description: result.error });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleClose() {
    setOpen(false);
    setResetData(null);
    setCopied(false);
    form.reset();
  }

  function handleOpenChange(value: boolean) {
    if (!value) {
      handleClose();
    } else {
      setOpen(true);
    }
  }

  async function copyToken() {
    if (!resetData) return;
    await navigator.clipboard.writeText(resetData.token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="size-4" />
          {t("createUser")}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        {resetData ? (
          <>
            <DialogHeader>
              <DialogTitle>{t("resetTokenTitle")}</DialogTitle>
              <DialogDescription>
                {t("resetTokenDescription")}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("resetToken")}</label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded-md bg-muted px-3 py-2 text-sm font-mono break-all">
                    {resetData.token}
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
                {copied && (
                  <p className="text-xs text-muted-foreground">{t("copied")}</p>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("resetUrl")}</label>
                <a
                  href={resetData.reset_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-md bg-muted px-3 py-2 text-sm text-primary underline break-all"
                >
                  {resetData.reset_url}
                </a>
              </div>
              <p className="text-sm text-muted-foreground">
                {t("validFor", { minutes: Math.floor(resetData.ttl / 60) })}
              </p>
            </div>
            <DialogFooter>
              <Button onClick={handleClose}>{t("close")}</Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>{t("createTitle")}</DialogTitle>
            </DialogHeader>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("username")}</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="displayName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("displayName")}</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("email")}</FormLabel>
                      <FormControl>
                        <Input type="email" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="phone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("phoneOptional")}</FormLabel>
                      <FormControl>
                        <Input type="tel" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="roles"
                  render={() => (
                    <FormItem>
                      <FormLabel>{t("selectRoles")}</FormLabel>
                      <div className="grid grid-cols-2 gap-3">
                        {ROLES.map((role) => (
                          <FormField
                            key={role}
                            control={form.control}
                            name="roles"
                            render={({ field }) => (
                              <FormItem className="flex items-center gap-2 space-y-0">
                                <FormControl>
                                  <Checkbox
                                    checked={field.value?.includes(role)}
                                    onCheckedChange={(checked) => {
                                      const current = field.value ?? [];
                                      field.onChange(
                                        checked
                                          ? [...current, role]
                                          : current.filter(
                                              (v: string) => v !== role,
                                            ),
                                      );
                                    }}
                                  />
                                </FormControl>
                                <FormLabel className="text-sm font-normal cursor-pointer">
                                  {tRoles(role)}
                                </FormLabel>
                              </FormItem>
                            )}
                          />
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleClose}
                  >
                    {t("cancel")}
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? t("creating") : t("create")}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Checkbox } from "@/components/ui/checkbox";
import { updateUserRoles } from "../_actions";

const ROLES = ["admin", "project_manager", "engineer", "field_worker"] as const;

const editRolesSchema = z.object({
  roles: z.array(z.string()).min(1, "At least one role required"),
});

type FormValues = z.infer<typeof editRolesSchema>;

interface EditRolesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  currentRoles: string[];
}

export function EditRolesDialog({
  open,
  onOpenChange,
  userId,
  currentRoles,
}: EditRolesDialogProps) {
  const t = useTranslations("users");
  const tRoles = useTranslations("roles");
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(editRolesSchema),
    defaultValues: {
      roles: currentRoles,
    },
  });

  // Reset form when dialog opens with fresh currentRoles
  React.useEffect(() => {
    if (open) {
      form.reset({ roles: currentRoles });
    }
  }, [open, currentRoles, form]);

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      const result = await updateUserRoles(userId, { roles: values.roles });
      if (result.success) {
        toast.success(t("rolesUpdated"));
        onOpenChange(false);
      } else {
        toast.error(t("actionError"), { description: result.error });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("editRoles")}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="roles"
              render={() => (
                <FormItem>
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
                onClick={() => onOpenChange(false)}
              >
                {t("cancel")}
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "..." : t("save")}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

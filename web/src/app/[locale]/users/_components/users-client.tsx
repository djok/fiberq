"use client";

import { useTranslations } from "next-intl";
import { DataTable } from "./data-table";
import { CreateUserDialog } from "./create-user-dialog";
import { getColumns } from "./columns";
import type { UserRow } from "@/types/user";

interface UsersClientProps {
  users: UserRow[];
  locale: string;
}

export function UsersClient({ users, locale }: UsersClientProps) {
  const t = useTranslations("users");
  const tRoles = useTranslations("roles");

  const columns = getColumns(
    {
      name: t("name"),
      email: t("email"),
      role: t("role"),
      status: t("status"),
      lastLogin: t("lastLogin"),
      actions: t("actions"),
      statusActive: t("statusActive"),
      statusInactive: t("statusInactive"),
      never: t("never"),
    },
    {
      admin: tRoles("admin"),
      project_manager: tRoles("project_manager"),
      engineer: tRoles("engineer"),
      field_worker: tRoles("field_worker"),
    },
    locale,
  );

  return (
    <DataTable
      columns={columns}
      data={users}
      createButton={<CreateUserDialog />}
    />
  );
}

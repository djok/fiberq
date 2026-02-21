"use client";

import type { Table } from "@tanstack/react-table";
import { useTranslations } from "next-intl";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { UserRow } from "@/types/user";

interface DataTableToolbarProps {
  table: Table<UserRow>;
  createButton?: React.ReactNode;
}

const ROLE_KEYS = ["admin", "project_manager", "engineer", "field_worker"];

export function DataTableToolbar({
  table,
  createButton,
}: DataTableToolbarProps) {
  const t = useTranslations("users");
  const tRoles = useTranslations("roles");

  return (
    <div className="flex items-center gap-2">
      <Input
        placeholder={t("searchPlaceholder")}
        value={table.getState().globalFilter ?? ""}
        onChange={(e) => table.setGlobalFilter(e.target.value)}
        className="max-w-sm"
      />

      <Select
        value={
          (table.getColumn("roles")?.getFilterValue() as string) ?? "all"
        }
        onValueChange={(value) =>
          table.getColumn("roles")?.setFilterValue(value === "all" ? "" : value)
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder={t("filterRole")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t("filterRole")}</SelectItem>
          {ROLE_KEYS.map((role) => (
            <SelectItem key={role} value={role}>
              {tRoles(role)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={
          (table.getColumn("isActive")?.getFilterValue() as string) ?? "all"
        }
        onValueChange={(value) =>
          table
            .getColumn("isActive")
            ?.setFilterValue(value === "all" ? "" : value)
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder={t("filterStatus")} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">{t("filterStatus")}</SelectItem>
          <SelectItem value="active">{t("statusActive")}</SelectItem>
          <SelectItem value="inactive">{t("statusInactive")}</SelectItem>
        </SelectContent>
      </Select>

      {createButton && <div className="ml-auto">{createButton}</div>}
    </div>
  );
}

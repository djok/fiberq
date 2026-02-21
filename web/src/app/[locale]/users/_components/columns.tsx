"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { ArrowUpDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UserActions } from "./user-actions";
import type { UserRow } from "@/types/user";

type Translations = {
  name: string;
  email: string;
  role: string;
  status: string;
  lastLogin: string;
  actions: string;
  statusActive: string;
  statusInactive: string;
  never: string;
};

type RoleTranslations = Record<string, string>;

export function getColumns(
  t: Translations,
  roles: RoleTranslations,
  locale: string,
): ColumnDef<UserRow>[] {
  return [
    {
      accessorKey: "displayName",
      header: ({ column }) => (
        <Button
          variant="ghost"
          size="sm"
          className="-ml-3"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          {t.name}
          <ArrowUpDown className="ml-2 size-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const inactive = !row.original.isActive;
        return (
          <div className={inactive ? "opacity-50" : ""}>
            <div className="font-medium">{row.original.displayName}</div>
            <div className="text-xs text-muted-foreground">
              {row.original.username}
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: "email",
      header: ({ column }) => (
        <Button
          variant="ghost"
          size="sm"
          className="-ml-3"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          {t.email}
          <ArrowUpDown className="ml-2 size-4" />
        </Button>
      ),
      cell: ({ row }) => {
        const inactive = !row.original.isActive;
        return (
          <span className={inactive ? "opacity-50" : ""}>
            {row.original.email}
          </span>
        );
      },
    },
    {
      accessorKey: "roles",
      header: t.role,
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1">
          {row.original.roles.map((role) => (
            <Badge key={role} variant="secondary">
              {roles[role] ?? role}
            </Badge>
          ))}
        </div>
      ),
      filterFn: (row, _columnId, filterValue: string) => {
        if (!filterValue || filterValue === "all") return true;
        return row.original.roles.includes(filterValue);
      },
    },
    {
      accessorKey: "isActive",
      header: t.status,
      cell: ({ row }) =>
        row.original.isActive ? (
          <Badge variant="default">{t.statusActive}</Badge>
        ) : (
          <Badge variant="destructive">{t.statusInactive}</Badge>
        ),
      filterFn: (row, _columnId, filterValue: string) => {
        if (!filterValue || filterValue === "all") return true;
        if (filterValue === "active") return row.original.isActive;
        if (filterValue === "inactive") return !row.original.isActive;
        return true;
      },
    },
    {
      accessorKey: "lastLogin",
      header: t.lastLogin,
      cell: ({ row }) => {
        const val = row.original.lastLogin;
        if (!val) return <span className="text-muted-foreground">{t.never}</span>;
        const d = new Date(val);
        return (
          <span>
            {d.toLocaleDateString(locale)} {d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}
          </span>
        );
      },
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <div onClick={(e) => e.stopPropagation()}>
          <UserActions user={row.original} />
        </div>
      ),
    },
  ];
}

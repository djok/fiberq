import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  UserCircle,
} from "lucide-react";

export const ROLES = {
  ADMIN: "admin",
  PROJECT_MANAGER: "project_manager",
  ENGINEER: "engineer",
  FIELD_WORKER: "field_worker",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

export interface NavItem {
  titleKey: string;
  href: string;
  icon: LucideIcon;
  requiredRoles?: Role[];
}

/**
 * Navigation items for the sidebar.
 * Items without requiredRoles are visible to all authenticated users.
 * Items with requiredRoles are visible only when the user has at least one matching role.
 */
export const NAV_ITEMS: NavItem[] = [
  {
    titleKey: "nav.dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    titleKey: "nav.projects",
    href: "/projects",
    icon: FolderKanban,
  },
  {
    titleKey: "nav.users",
    href: "/users",
    icon: Users,
    requiredRoles: ["admin"],
  },
  {
    titleKey: "nav.profile",
    href: "/profile",
    icon: UserCircle,
  },
];

/**
 * Filter navigation items based on user roles.
 * Items without requiredRoles are always shown.
 * Items with requiredRoles need at least one matching role.
 */
export function filterNavByRole(
  items: NavItem[],
  userRoles: string[],
): NavItem[] {
  return items.filter((item) => {
    if (!item.requiredRoles || item.requiredRoles.length === 0) return true;
    return item.requiredRoles.some((role) => userRoles.includes(role));
  });
}

/**
 * Get the default redirect path based on user roles.
 * Admin goes to User Management, others go to Projects.
 */
export function getDefaultRedirect(roles: string[]): string {
  if (roles.includes("admin")) {
    return "/users";
  }
  return "/projects";
}

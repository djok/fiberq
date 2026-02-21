"use client";

import { useTranslations } from "next-intl";
import { usePathname, Link } from "@/i18n/navigation";
import { NAV_ITEMS, filterNavByRole } from "@/lib/roles";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export function SidebarNav({ roles }: { roles: string[] }) {
  const t = useTranslations();
  const pathname = usePathname();
  const visibleItems = filterNavByRole(NAV_ITEMS, roles);

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{t("nav.navigation", { defaultValue: "Navigation" })}</SidebarGroupLabel>
      <SidebarMenu>
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <SidebarMenuItem key={item.href}>
              <SidebarMenuButton
                asChild
                isActive={isActive}
                tooltip={t(item.titleKey)}
              >
                <Link href={item.href}>
                  <Icon />
                  <span>{t(item.titleKey)}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}

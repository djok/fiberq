import type { Session } from "next-auth";
import Image from "next/image";
import { Link } from "@/i18n/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { SidebarNav } from "@/components/sidebar-nav";
import { UserNav } from "@/components/user-nav";

export function AppSidebar({ session }: { session: Session }) {
  return (
    <Sidebar collapsible="icon" variant="sidebar">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/">
                <Image
                  src="/logo.svg"
                  alt="FiberQ"
                  width={24}
                  height={24}
                  className="shrink-0"
                />
                <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                  <span className="truncate font-semibold">FiberQ</span>
                  <span className="truncate text-xs text-muted-foreground">
                    Fiber Network Manager
                  </span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarNav roles={session.user.roles} />
      </SidebarContent>
      <SidebarFooter>
        <UserNav session={session} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

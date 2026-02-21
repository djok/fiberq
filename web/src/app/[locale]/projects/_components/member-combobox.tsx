"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { assignMember, fetchAssignableUsers } from "../_actions";
import type { AssignableUser } from "@/types/project";

interface MemberComboboxProps {
  projectId: number;
  existingMemberSubs: string[];
}

const PROJECT_ROLES = ["manager", "specialist", "observer"] as const;

const ROLE_LABEL_MAP: Record<string, string> = {
  manager: "roleManager",
  specialist: "roleSpecialist",
  observer: "roleObserver",
};

export function MemberCombobox({
  projectId,
  existingMemberSubs,
}: MemberComboboxProps) {
  const t = useTranslations("projects");
  const router = useRouter();

  const [open, setOpen] = React.useState(false);
  const [users, setUsers] = React.useState<AssignableUser[]>([]);
  const [selectedUser, setSelectedUser] = React.useState<AssignableUser | null>(
    null,
  );
  const [selectedRole, setSelectedRole] = React.useState<string>("specialist");
  const [isAssigning, setIsAssigning] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  // Fetch users when popover opens
  React.useEffect(() => {
    if (!open) return;
    let cancelled = false;

    async function loadUsers() {
      setIsLoading(true);
      const result = await fetchAssignableUsers(projectId);
      if (cancelled) return;
      if (result.success) {
        setUsers(result.data);
      }
      setIsLoading(false);
    }

    loadUsers();
    return () => {
      cancelled = true;
    };
  }, [open, projectId]);

  // Filter out already-assigned users
  const availableUsers = users.filter(
    (u) => !existingMemberSubs.includes(u.userSub),
  );

  async function handleAssign() {
    if (!selectedUser || !selectedRole) return;
    setIsAssigning(true);
    try {
      const result = await assignMember(projectId, {
        user_sub: selectedUser.userSub,
        user_display_name: selectedUser.displayName ?? undefined,
        user_email: selectedUser.email ?? undefined,
        project_role: selectedRole,
      });

      if (result.success) {
        toast.success(t("assignSuccess"));
        setSelectedUser(null);
        setSelectedRole("specialist");
        router.refresh();
      } else {
        toast.error(result.error);
      }
    } finally {
      setIsAssigning(false);
    }
  }

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="flex-1 justify-between"
          >
            <span className="truncate">
              {selectedUser
                ? selectedUser.displayName || selectedUser.userSub
                : t("selectUser")}
            </span>
            <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[280px] p-0" align="start">
          <Command>
            <CommandInput placeholder={t("searchUsers")} />
            <CommandList>
              <CommandEmpty>
                {isLoading ? "..." : t("noUsersFound")}
              </CommandEmpty>
              <CommandGroup>
                {availableUsers.map((user) => (
                  <CommandItem
                    key={user.userSub}
                    value={`${user.displayName ?? ""} ${user.email ?? ""}`}
                    onSelect={() => {
                      setSelectedUser(user);
                      setOpen(false);
                    }}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-sm truncate">
                        {user.displayName || user.userSub}
                      </div>
                      {user.email && (
                        <div className="text-xs text-muted-foreground truncate">
                          {user.email}
                        </div>
                      )}
                    </div>
                    <Check
                      className={cn(
                        "ml-auto size-4",
                        selectedUser?.userSub === user.userSub
                          ? "opacity-100"
                          : "opacity-0",
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      <Select value={selectedRole} onValueChange={setSelectedRole}>
        <SelectTrigger className="w-[140px] shrink-0">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {PROJECT_ROLES.map((role) => (
            <SelectItem key={role} value={role}>
              {t(ROLE_LABEL_MAP[role])}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button
        size="sm"
        className="shrink-0"
        onClick={handleAssign}
        disabled={!selectedUser || isAssigning}
      >
        {isAssigning ? "..." : t("addMember")}
      </Button>
    </div>
  );
}

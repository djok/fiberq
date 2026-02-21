import {
  Upload,
  UserPlus,
  UserMinus,
  ArrowRightLeft,
  CalendarDays,
} from "lucide-react";
import type { ActivityEntry } from "@/types/project";

interface Translations {
  today: string;
  yesterday: string;
  syncUpload: string;
  memberAssigned: string;
  memberRemoved: string;
  statusChanged: string;
  unknownUser: string;
}

interface ActivityTimelineProps {
  entries: ActivityEntry[];
  locale: string;
  translations: Translations;
}

function getDayKey(dateStr: string, locale: string, t: Translations): string {
  const date = new Date(dateStr);
  const now = new Date();

  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const diff = todayOnly.getTime() - dateOnly.getTime();
  const dayMs = 86400000;

  if (diff < dayMs && diff >= 0) return t.today;
  if (diff >= dayMs && diff < dayMs * 2) return t.yesterday;
  return date.toLocaleDateString(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function getEventIcon(eventType: string) {
  switch (eventType) {
    case "sync_upload":
      return {
        icon: <Upload className="size-4" />,
        bg: "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",
      };
    case "member_assigned":
      return {
        icon: <UserPlus className="size-4" />,
        bg: "bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400",
      };
    case "member_removed":
      return {
        icon: <UserMinus className="size-4" />,
        bg: "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400",
      };
    case "status_change":
      return {
        icon: <ArrowRightLeft className="size-4" />,
        bg: "bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400",
      };
    default:
      return {
        icon: <CalendarDays className="size-4" />,
        bg: "bg-muted text-muted-foreground",
      };
  }
}

function buildEventMessage(entry: ActivityEntry, t: Translations): string {
  const user = entry.userDisplayName || t.unknownUser;
  const details = entry.details || {};

  switch (entry.eventType) {
    case "sync_upload": {
      const count = (details.features_uploaded as number) ?? 0;
      return t.syncUpload
        .replace("{user}", user)
        .replace("{count}", String(count));
    }
    case "member_assigned": {
      const member =
        (details.member_name as string) || (details.user_display_name as string) || user;
      const role = (details.project_role as string) ?? "";
      return t.memberAssigned
        .replace("{member}", member)
        .replace("{role}", role);
    }
    case "member_removed": {
      const member =
        (details.member_name as string) || (details.user_display_name as string) || user;
      return t.memberRemoved.replace("{member}", member);
    }
    case "status_change": {
      const oldStatus = (details.old_status as string) ?? "";
      const newStatus = (details.new_status as string) ?? "";
      return t.statusChanged
        .replace("{from}", oldStatus)
        .replace("{to}", newStatus);
    }
    default:
      return entry.eventType;
  }
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

type DayGroup = {
  label: string;
  entries: ActivityEntry[];
};

function groupByDay(
  entries: ActivityEntry[],
  locale: string,
  t: Translations,
): DayGroup[] {
  const groups: DayGroup[] = [];
  let currentLabel = "";
  let currentEntries: ActivityEntry[] = [];

  for (const entry of entries) {
    const label = getDayKey(entry.eventAt, locale, t);
    if (label !== currentLabel) {
      if (currentEntries.length > 0) {
        groups.push({ label: currentLabel, entries: currentEntries });
      }
      currentLabel = label;
      currentEntries = [entry];
    } else {
      currentEntries.push(entry);
    }
  }
  if (currentEntries.length > 0) {
    groups.push({ label: currentLabel, entries: currentEntries });
  }
  return groups;
}

export function ActivityTimeline({
  entries,
  locale,
  translations,
}: ActivityTimelineProps) {
  const groups = groupByDay(entries, locale, translations);

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <div key={group.label}>
          {/* Day header */}
          <div className="flex items-center gap-2 mb-3">
            <div className="flex size-6 items-center justify-center rounded-full border bg-background">
              <CalendarDays className="size-3 text-muted-foreground" />
            </div>
            <span className="text-sm font-medium text-muted-foreground">
              {group.label}
            </span>
          </div>

          {/* Entries */}
          <div className="relative ml-3 space-y-0">
            {group.entries.map((entry, idx) => {
              const { icon, bg } = getEventIcon(entry.eventType);
              const message = buildEventMessage(entry, translations);
              const isLast = idx === group.entries.length - 1;

              return (
                <div key={`${entry.eventAt}-${idx}`} className="relative flex gap-3 pb-4">
                  {/* Vertical line */}
                  {!isLast && (
                    <div className="absolute left-4 top-8 bottom-0 w-px bg-border" />
                  )}
                  {/* Event icon */}
                  <div
                    className={`flex size-8 shrink-0 items-center justify-center rounded-full ${bg}`}
                  >
                    {icon}
                  </div>
                  {/* Event content */}
                  <div className="min-w-0 flex-1 pt-0.5">
                    <p className="text-sm">{message}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatTime(entry.eventAt)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

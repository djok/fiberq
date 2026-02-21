"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { Inbox, Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ActivityTimeline } from "./activity-timeline";
import { fetchActivity } from "../_actions";
import type { ActivityEntry } from "@/types/project";

interface ProjectActivityProps {
  projectId: number;
  initialEntries: ActivityEntry[];
  initialHasMore: boolean;
  locale: string;
}

export function ProjectActivity({
  projectId,
  initialEntries,
  initialHasMore,
  locale,
}: ProjectActivityProps) {
  const t = useTranslations("dashboard");
  const [entries, setEntries] = React.useState(initialEntries);
  const [hasMore, setHasMore] = React.useState(initialHasMore);
  const [loading, setLoading] = React.useState(false);

  const translations = React.useMemo(
    () => ({
      today: t("today"),
      yesterday: t("yesterday"),
      syncUpload: t("syncUpload"),
      memberAssigned: t("memberAssigned"),
      memberRemoved: t("memberRemoved"),
      statusChanged: t("statusChanged"),
      unknownUser: t("unknownUser"),
    }),
    [t],
  );

  async function handleLoadMore() {
    if (entries.length === 0 || loading) return;
    setLoading(true);

    const lastEntry = entries[entries.length - 1];
    const result = await fetchActivity(projectId, lastEntry.eventAt);

    if (result.success) {
      setEntries((prev) => [...prev, ...result.data.entries]);
      setHasMore(result.data.hasMore);
    }

    setLoading(false);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("activity")}</CardTitle>
      </CardHeader>
      <CardContent>
        {entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Inbox className="size-10 text-muted-foreground mb-3" />
            <p className="text-sm font-medium text-muted-foreground">
              {t("noActivity")}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {t("noActivityDescription")}
            </p>
          </div>
        ) : (
          <>
            <ActivityTimeline
              entries={entries}
              locale={locale}
              translations={translations}
            />
            {hasMore && (
              <Button
                variant="outline"
                size="sm"
                className="w-full mt-4"
                onClick={handleLoadMore}
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="size-4 animate-spin mr-2" />
                ) : null}
                {t("loadMore")}
              </Button>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

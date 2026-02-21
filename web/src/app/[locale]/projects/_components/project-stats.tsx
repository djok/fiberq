import { Box, Zap, Cable, Ruler, Users, Clock } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { StatTile } from "./stat-tile";
import type { ProjectStats as ProjectStatsType } from "@/types/project";

interface ProjectStatsProps {
  stats: ProjectStatsType;
  lastSyncRelative: string | null;
  lastSyncExact: string | null;
  translations: {
    closures: string;
    poles: string;
    cables: string;
    cableLength: string;
    teamSize: string;
    lastSync: string;
  };
}

function formatCableLength(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`;
  }
  return `${meters} m`;
}

export function ProjectStats({
  stats,
  lastSyncRelative,
  lastSyncExact,
  translations: t,
}: ProjectStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatTile
        icon={<Box className="size-5" />}
        label={t.closures}
        value={stats.closures}
      />
      <StatTile
        icon={<Zap className="size-5" />}
        label={t.poles}
        value={stats.poles}
      />
      <StatTile
        icon={<Cable className="size-5" />}
        label={t.cables}
        value={stats.cables}
      />
      <StatTile
        icon={<Ruler className="size-5" />}
        label={t.cableLength}
        value={stats.cableLengthM}
        formatValue={formatCableLength}
      />
      <StatTile
        icon={<Users className="size-5" />}
        label={t.teamSize}
        value={stats.teamSize}
      />
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <StatTile
                icon={<Clock className="size-5" />}
                label={t.lastSync}
                value={lastSyncRelative}
                delta={stats.lastSyncFeatures}
              />
            </div>
          </TooltipTrigger>
          {lastSyncExact && (
            <TooltipContent>
              <p>{lastSyncExact}</p>
            </TooltipContent>
          )}
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}

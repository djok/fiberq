import type { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface StatTileProps {
  icon: ReactNode;
  label: string;
  value: number | string | null;
  delta?: number | null;
  formatValue?: (v: number) => string;
}

export function StatTile({
  icon,
  label,
  value,
  delta,
  formatValue,
}: StatTileProps) {
  let displayValue: string;
  if (value === null) {
    displayValue = "\u2014";
  } else if (typeof value === "string") {
    displayValue = value;
  } else if (formatValue) {
    displayValue = formatValue(value);
  } else {
    displayValue = value.toLocaleString();
  }

  return (
    <Card className="py-4">
      <CardContent className="flex items-center gap-3 px-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          {icon}
        </div>
        <div className="min-w-0">
          <p className="text-sm text-muted-foreground truncate">{label}</p>
          <p className="text-2xl font-bold leading-tight">{displayValue}</p>
          {delta != null && delta !== 0 && (
            <p
              className={`text-xs ${
                delta > 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
              }`}
            >
              {delta > 0 ? `+${delta}` : delta}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

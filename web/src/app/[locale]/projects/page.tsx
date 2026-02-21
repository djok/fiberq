import { setRequestLocale, getTranslations } from "next-intl/server";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default async function ProjectsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const tNav = await getTranslations("nav");
  const tPlaceholder = await getTranslations("placeholder");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-semibold">{tNav("projects")}</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base text-muted-foreground">
            {tPlaceholder("comingSoon")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-6 text-sm text-muted-foreground">
            {tPlaceholder("projects")}
          </p>

          {/* Skeleton table layout */}
          <div className="space-y-3">
            {/* Table header skeleton */}
            <div className="flex items-center gap-4 border-b pb-2">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-4 w-1/6" />
              <Skeleton className="h-4 w-1/6" />
              <Skeleton className="h-4 w-1/4" />
            </div>
            {/* Table rows skeleton */}
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 py-2">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-4 w-1/6" />
                <Skeleton className="h-4 w-1/6" />
                <Skeleton className="h-4 w-1/4" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { getTranslations } from "next-intl/server";
import { ExternalLink, Mail, Shield, Clock, FolderKanban } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

function getInitials(name?: string | null): string {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (
    parts[0].charAt(0) + parts[parts.length - 1].charAt(0)
  ).toUpperCase();
}

interface ProfileCardProps {
  user: {
    name?: string | null;
    email?: string | null;
    image?: string | null;
    roles: string[];
  };
  locale: string;
  authTime?: number | null;
}

export async function ProfileCard({
  user,
  locale,
  authTime,
}: ProfileCardProps) {
  const t = await getTranslations("profile");
  const tRoles = await getTranslations("roles");

  const zitadelIssuer = process.env.ZITADEL_ISSUER;
  const editProfileUrl = zitadelIssuer
    ? `${zitadelIssuer}/ui/console/users/me`
    : "#";

  const lastLoginDisplay = authTime
    ? new Date(authTime * 1000).toLocaleString(locale)
    : "N/A";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start gap-4">
          <Avatar className="h-20 w-20 rounded-lg" size="default">
            <AvatarImage src={user.image ?? undefined} alt={user.name ?? ""} />
            <AvatarFallback className="rounded-lg text-xl">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col gap-1.5">
            <h2 className="text-xl font-semibold">{user.name ?? "—"}</h2>
            <p className="text-sm text-muted-foreground">{user.email}</p>
            <div className="flex flex-wrap gap-1.5">
              {user.roles.length > 0 ? (
                user.roles.map((role) => (
                  <Badge key={role} variant="secondary">
                    {tRoles.has(role) ? tRoles(role) : role}
                  </Badge>
                ))
              ) : (
                <Badge variant="outline">—</Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="flex items-start gap-3">
            <Mail className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                {t("email")}
              </p>
              <p className="text-sm">{user.email ?? "—"}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                {t("role")}
              </p>
              <p className="text-sm">
                {user.roles
                  .map((role) => (tRoles.has(role) ? tRoles(role) : role))
                  .join(", ") || "—"}
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Clock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                {t("lastLogin")}
              </p>
              <p className="text-sm">{lastLoginDisplay}</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <FolderKanban className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                {t("projects")}
              </p>
              <p className="text-sm text-muted-foreground">
                {t("noProjects")}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="outline" size="sm" asChild>
          <a
            href={editProfileUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            {t("editProfile")}
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}

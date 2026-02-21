import { setRequestLocale, getTranslations } from "next-intl/server";
import { auth } from "@/auth";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { UserDetailActions } from "../_components/user-detail-actions";
import type { UserRow } from "@/types/user";

type ApiUser = {
  id: string;
  username: string;
  display_name: string;
  email: string;
  phone: string | null;
  roles: string[];
  is_active: boolean;
  last_login: string | null;
};

function mapUser(u: ApiUser): UserRow {
  return {
    id: u.id,
    username: u.username,
    displayName: u.display_name,
    email: u.email,
    phone: u.phone,
    roles: u.roles,
    isActive: u.is_active,
    lastLogin: u.last_login,
  };
}

export default async function UserDetailPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session || !session.user.roles.includes("admin")) {
    notFound();
  }

  const t = await getTranslations("users");

  let user: UserRow;
  try {
    const data = await apiFetch<ApiUser>(`/users/${id}`);
    user = mapUser(data);
  } catch {
    notFound();
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-4">
        <Link
          href={`/${locale}/users`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-4" />
          {t("backToUsers")}
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">{user.displayName}</h1>
        {user.isActive ? (
          <Badge variant="default">{t("statusActive")}</Badge>
        ) : (
          <Badge variant="destructive">{t("statusInactive")}</Badge>
        )}
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Profile Information Card */}
          <Card>
            <CardHeader>
              <CardTitle>{t("profileInfo")}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t("displayName")}
                  </p>
                  <p className="text-sm mt-1">{user.displayName}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">
                    {t("username")}
                  </p>
                  <p className="text-sm mt-1">{user.username}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t("email")}</p>
                  <p className="text-sm mt-1">{user.email}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t("phone")}</p>
                  <p className="text-sm mt-1">
                    {user.phone || t("notSet")}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Client component for interactive actions */}
        <div className="space-y-6">
          <UserDetailActions user={user} locale={locale} />
        </div>
      </div>
    </div>
  );
}

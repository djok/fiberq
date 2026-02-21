import { setRequestLocale, getTranslations } from "next-intl/server";
import { auth } from "@/auth";
import { notFound } from "next/navigation";
import { apiFetch } from "@/lib/api";
import type { UserRow } from "@/types/user";
import { UsersClient } from "./_components/users-client";

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

type ApiResponse = {
  users: ApiUser[];
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

export default async function UsersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session || !session.user.roles.includes("admin")) {
    notFound();
  }

  const t = await getTranslations("users");

  let users: UserRow[] = [];
  try {
    const data = await apiFetch<ApiResponse>("/users");
    users = data.users.map(mapUser);
  } catch {
    // API unavailable -- show empty table
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-semibold">{t("title")}</h1>
      <UsersClient users={users} locale={locale} />
    </div>
  );
}

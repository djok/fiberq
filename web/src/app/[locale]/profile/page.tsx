import { setRequestLocale, getTranslations } from "next-intl/server";
import { auth } from "@/auth";
import { redirect } from "next/navigation";
import { ProfileCard } from "@/components/profile-card";

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);

  const session = await auth();
  if (!session) {
    redirect("/api/auth/signin/zitadel");
  }

  const t = await getTranslations("profile");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">{t("title")}</h1>
      <ProfileCard user={session.user} locale={locale} />
    </div>
  );
}

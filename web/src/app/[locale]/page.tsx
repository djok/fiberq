import { auth } from "@/auth";
import { getDefaultRedirect } from "@/lib/roles";
import { redirect } from "@/i18n/navigation";
import { getLocale } from "next-intl/server";

export default async function LocaleRootPage() {
  const session = await auth();
  const locale = await getLocale();

  if (!session) {
    // Fallback -- layout should have already redirected
    redirect({ href: "/api/auth/signin/zitadel", locale });
    return null;
  }

  const target = getDefaultRedirect(session.user.roles);
  redirect({ href: target, locale });
}

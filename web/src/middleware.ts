import { auth } from "./auth";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const intlMiddleware = createIntlMiddleware(routing);

/**
 * Next.js 16 proxy: composes auth check THEN i18n routing.
 *
 * CRITICAL ordering: Auth check runs BEFORE i18n middleware.
 * If reversed, unauthenticated users get locale-redirected instead of
 * login-redirected, causing redirect loops (Pitfall #7).
 */
export default auth(async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip auth for NextAuth API routes (callbacks, signin, signout)
  if (pathname.startsWith("/api/auth")) {
    return NextResponse.next();
  }

  // Skip auth for other API routes (proxied to FastAPI)
  if (pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // Check authentication via Auth.js
  // auth() wraps this function and attaches the session to request.auth
  const session = (request as unknown as { auth: unknown }).auth;
  if (!session) {
    // Redirect directly to Kanidm login (no intermediate landing page)
    const signInUrl = new URL("/api/auth/signin", request.url);
    return NextResponse.redirect(signInUrl);
  }

  // Apply i18n routing for authenticated requests
  return intlMiddleware(request);
});

export const config = {
  matcher: "/((?!_next|_vercel|.*\\..*).*)",
};

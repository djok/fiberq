import NextAuth from "next-auth";

const KANIDM_ROLE_PREFIX = "fiberq_";

/**
 * Extract FiberQ roles from Kanidm token claims.
 * Kanidm provides group membership in the "groups" claim when the
 * "groups" scope is requested. Groups are returned as an array of names.
 * We filter for groups with the "fiberq_" prefix and strip it to get roles.
 */
function extractRolesFromClaims(claims: Record<string, unknown>): string[] {
  const groups = claims["groups"];
  if (!Array.isArray(groups)) return [];

  return groups
    .filter(
      (g): g is string =>
        typeof g === "string" && g.startsWith(KANIDM_ROLE_PREFIX),
    )
    .map((g) => g.slice(KANIDM_ROLE_PREFIX.length));
}

/**
 * Decode JWT payload without verification.
 * The token was already verified by the OIDC flow -- we just need the claims.
 */
function decodeJwtPayload(token: string): Record<string, unknown> {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return {};
    const payload = parts[1];
    const decoded = Buffer.from(payload, "base64url").toString("utf-8");
    return JSON.parse(decoded);
  } catch {
    return {};
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    {
      id: "kanidm",
      name: "Kanidm",
      type: "oidc",
      issuer: `${process.env.KANIDM_URL}/oauth2/openid/${process.env.AUTH_KANIDM_ID}`,
      clientId: process.env.AUTH_KANIDM_ID!,
      clientSecret: process.env.AUTH_KANIDM_SECRET!,
      authorization: {
        params: {
          scope: "openid profile email groups",
        },
      },
    },
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account }) {
      // On initial sign-in: capture raw Kanidm tokens
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.idToken = account.id_token;
        token.expiresAt = account.expires_at;

        // Extract roles from the id_token or access_token claims
        const idClaims = account.id_token
          ? decodeJwtPayload(account.id_token)
          : {};
        const accessClaims = account.access_token
          ? decodeJwtPayload(account.access_token)
          : {};

        // Try id_token first, fall back to access_token
        let roles = extractRolesFromClaims(idClaims);
        if (roles.length === 0) {
          roles = extractRolesFromClaims(accessClaims);
        }
        token.roles = roles;

        // Record login event for last-login tracking (fire-and-forget)
        const apiUrl = process.env.INTERNAL_API_URL || "http://api:8000";
        fetch(`${apiUrl}/auth/record-login`, {
          method: "POST",
          headers: { Authorization: `Bearer ${account.access_token}` },
        }).catch(() => {}); // Don't block sign-in if this fails
      }

      // Silent token refresh when access_token expires
      const expiresAt = token.expiresAt as number | undefined;
      if (expiresAt && Date.now() / 1000 > expiresAt) {
        try {
          const response = await fetch(
            `${process.env.KANIDM_URL}/oauth2/token`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/x-www-form-urlencoded",
              },
              body: new URLSearchParams({
                grant_type: "refresh_token",
                client_id: process.env.AUTH_KANIDM_ID!,
                client_secret: process.env.AUTH_KANIDM_SECRET!,
                refresh_token: token.refreshToken as string,
              }),
            },
          );

          if (!response.ok) {
            throw new Error(`Refresh failed: ${response.status}`);
          }

          const refreshed = await response.json();

          token.accessToken = refreshed.access_token;
          token.expiresAt = Math.floor(
            Date.now() / 1000 + refreshed.expires_in,
          );
          if (refreshed.refresh_token) {
            token.refreshToken = refreshed.refresh_token;
          }
          if (refreshed.id_token) {
            token.idToken = refreshed.id_token;
          }

          // Re-extract roles from refreshed token
          const claims = decodeJwtPayload(refreshed.access_token);
          const roles = extractRolesFromClaims(claims);
          if (roles.length > 0) {
            token.roles = roles;
          }

          // Clear any previous error
          delete token.error;
        } catch (error) {
          console.error("Token refresh failed:", error);
          token.error = "RefreshTokenError";
        }
      }

      return token;
    },
    async session({ session, token }) {
      // Forward the RAW Kanidm access_token to the session.
      // CRITICAL: This is the raw Kanidm JWT (ES256), NOT the NextAuth JWE.
      // FastAPI validates this against Kanidm's JWKS.
      session.accessToken = token.accessToken as string;
      session.idToken = token.idToken as string;
      session.user.roles = (token.roles as string[]) ?? [];

      if (token.error) {
        session.error = token.error as string;
      }

      return session;
    },
  },
});

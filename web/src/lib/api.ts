import { auth } from "@/auth";

const API_BASE = process.env.INTERNAL_API_URL || "http://api:8000";

/**
 * Server-side fetch helper that forwards the raw Zitadel JWT to FastAPI.
 *
 * CRITICAL: Uses session.accessToken which is the raw Zitadel-issued JWT,
 * NOT the NextAuth encrypted session token. FastAPI validates it against
 * Zitadel's JWKS endpoint.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const session = await auth();
  if (!session?.accessToken) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${session.accessToken}`,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

/**
 * Fetch additional user profile data from Zitadel's userinfo endpoint.
 * Returns claims like auth_time (last login) and picture (avatar URL)
 * that may not be in the standard OIDC session claims.
 */
export async function fetchUserInfo(): Promise<Record<
  string,
  unknown
> | null> {
  const session = await auth();
  if (!session?.accessToken) return null;

  const issuer = process.env.ZITADEL_ISSUER;
  if (!issuer) return null;

  try {
    const res = await fetch(`${issuer}/oidc/v1/userinfo`, {
      headers: { Authorization: `Bearer ${session.accessToken}` },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

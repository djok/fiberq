import type { NextAuthConfig } from "next-auth";

/**
 * Edge-compatible auth config (no database adapter, no Node.js APIs).
 * Used by proxy.ts for lightweight auth checks.
 */
export const authConfig: NextAuthConfig = {
  pages: {},
  providers: [], // Full providers defined in auth.ts
  callbacks: {
    authorized({ auth }) {
      return !!auth;
    },
  },
};

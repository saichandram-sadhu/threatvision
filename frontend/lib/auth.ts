import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GithubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";

import { fetchThreatvisionApi } from "@/lib/threatvisionServerFetch";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;
        const res = await fetchThreatvisionApi("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials.email.trim().toLowerCase(),
            password: credentials.password,
          }),
        });
        const text = await res.text();
        if (!res.ok) {
          if (res.status === 422) {
            throw new Error(
              "Login request rejected by API (422). Restart the FastAPI server after code updates, or sign in with admin@threatvision.dev / admin.",
            );
          }
          if (res.status === 503) {
            let msg =
              "Database unavailable — start PostgreSQL (docker compose up -d in threatvision/).";
            try {
              const j = JSON.parse(text) as { detail?: string };
              if (j.detail) msg = String(j.detail);
            } catch {
              /* keep default */
            }
            throw new Error(msg);
          }
          if (res.status === 502) {
            let msg = "Cannot reach ThreatVision API — start the backend on 127.0.0.1:8001.";
            try {
              const j = JSON.parse(text) as { detail?: string };
              if (j.detail) msg = String(j.detail);
            } catch {
              /* keep default */
            }
            throw new Error(msg);
          }
          return null;
        }
        const data = JSON.parse(text) as {
          user_id: string;
          email: string;
          role: string;
        };
        return {
          id: data.user_id,
          email: data.email,
          role: data.role,
        };
      },
    }),
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    ...(process.env.GITHUB_ID && process.env.GITHUB_SECRET
      ? [
          GithubProvider({
            clientId: process.env.GITHUB_ID,
            clientSecret: process.env.GITHUB_SECRET,
          }),
        ]
      : []),
  ],
  session: { strategy: "jwt", maxAge: 60 * 60 * 24 * 7 },
  pages: { signIn: "/login" },
  callbacks: {
    async jwt({ token, user, account }) {
      if (account?.provider === "credentials" && user) {
        token.id = user.id;
        token.role = user.role ?? "USER";
        token.email = user.email ?? token.email;
      } else if (account && account.provider !== "credentials") {
        token.id = `${account.provider}:${account.providerAccountId}`;
        token.role = "USER";
        token.email = user?.email ?? token.email;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = (token.id as string) || "";
        session.user.role = (token.role as string) ?? "USER";
        if (token.email) session.user.email = token.email as string;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};

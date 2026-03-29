/**
 * Server-side BFF helpers: exchange internal JWT then call FastAPI.
 * Never expose BFF_SERVICE_KEY or internal JWT to the browser.
 */

import { getServerSession } from "next-auth";

import { authOptions } from "@/lib/auth";

export function getBackendUrl(): string {
  const u = process.env.BACKEND_URL?.trim() || "http://localhost:8000";
  return u.replace(/\/$/, "");
}

/** UUID v4 pattern — OAuth sessions use non-UUID ids and cannot call the BFF exchange yet. */
export function isBackendLinkedUserId(id: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    id,
  );
}

export async function exchangeInternalJwt(userId: string, role: string): Promise<string> {
  const key = process.env.BFF_SERVICE_KEY;
  if (!key) {
    throw new Error("BFF_SERVICE_KEY is not configured");
  }
  const res = await fetch(`${getBackendUrl()}/internal/auth/exchange`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Service-Key": key,
    },
    body: JSON.stringify({ user_id: userId, role }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Internal JWT exchange failed (${res.status}): ${text.slice(0, 200)}`);
  }
  const data = (await res.json()) as { access_token: string };
  return data.access_token;
}

export type FetchBackendSession = {
  user: { id: string; role: string };
};

function requestInitWithoutSession(
  init?: RequestInit & { session?: FetchBackendSession | null },
): RequestInit {
  if (!init) return {};
  const copy = { ...init } as RequestInit & { session?: unknown };
  delete copy.session;
  return copy;
}

/**
 * Authenticated FastAPI request using a fresh internal JWT (one exchange per call).
 * Pass ``session`` from a Route Handler if you already called ``getServerSession``.
 */
export async function fetchBackend(
  path: string,
  init?: RequestInit & { session?: FetchBackendSession | null },
): Promise<Response> {
  const session = init?.session ?? (await getServerSession(authOptions));
  if (!session?.user?.id) {
    throw new Error("Not authenticated");
  }
  if (!isBackendLinkedUserId(session.user.id)) {
    throw new Error(
      "This account is not linked to ThreatVision yet. Sign in with email and password.",
    );
  }
  const fetchInit = requestInitWithoutSession(init);
  const token = await exchangeInternalJwt(session.user.id, session.user.role);
  const url = `${getBackendUrl()}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(fetchInit.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...fetchInit, headers });
}

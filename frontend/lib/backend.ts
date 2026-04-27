/**
 * Server-side BFF helpers: exchange internal JWT then call FastAPI.
 * Never expose BFF_SERVICE_KEY or internal JWT to the browser.
 */

import { getServerSession } from "next-auth";

import { authOptions } from "@/lib/auth";

/** Default matches local README (port 8001 avoids common clash with other apps on :8000). */
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8001";

export function getBackendUrl(): string {
  const u = process.env.BACKEND_URL?.trim() || DEFAULT_BACKEND_URL;
  return u.replace(/\/$/, "");
}

/** UUID v4 pattern — OAuth sessions use non-UUID ids and cannot call the BFF exchange yet. */
export function isBackendLinkedUserId(id: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    id,
  );
}

/**
 * Exchange internal JWT and return the API origin that accepted it.
 * Tries ``BACKEND_URL`` first, then ``127.0.0.1:8001`` when the first returns 404 (wrong app on :8000).
 */
export async function getInternalJwtAndApiBase(
  userId: string,
  role: string,
): Promise<{ token: string; apiBase: string }> {
  const key = process.env.BFF_SERVICE_KEY;
  if (!key) {
    throw new Error("BFF_SERVICE_KEY is not configured");
  }
  const body = JSON.stringify({ user_id: userId, role });
  const hdrs: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Service-Key": key,
  };

  const candidates = [
    getBackendUrl().replace(/\/$/, ""),
    DEFAULT_BACKEND_URL.replace(/\/$/, ""),
  ];
  const seen = new Set<string>();
  let lastStatus = 0;
  let lastText = "";

  for (const apiBase of candidates) {
    if (seen.has(apiBase)) continue;
    seen.add(apiBase);
    const res = await fetch(`${apiBase}/internal/auth/exchange`, {
      method: "POST",
      headers: hdrs,
      body,
    });
    if (res.ok) {
      const data = (await res.json()) as { access_token: string };
      return { token: data.access_token, apiBase };
    }
    lastStatus = res.status;
    lastText = await res.text();
    if (res.status !== 404) {
      break;
    }
  }

  throw new Error(`Internal JWT exchange failed (${lastStatus}): ${lastText.slice(0, 200)}`);
}

export async function exchangeInternalJwt(userId: string, role: string): Promise<string> {
  const { token } = await getInternalJwtAndApiBase(userId, role);
  return token;
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
  const { token, apiBase } = await getInternalJwtAndApiBase(session.user.id, session.user.role);
  const url = `${apiBase}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(fetchInit.headers);
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...fetchInit, headers });
}

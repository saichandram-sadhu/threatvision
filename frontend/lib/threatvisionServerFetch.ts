/**
 * Server-only: call FastAPI from Next.js when BACKEND_URL may wrongly point at :8000 (other apps).
 * Retries on 404 or connection error against local ThreatVision default (8001).
 */
import { getBackendUrl } from "@/lib/backend";

const LOCAL_THREATVISION = "http://127.0.0.1:8001";

export async function fetchThreatvisionApi(path: string, init: RequestInit): Promise<Response> {
  const p = path.startsWith("/") ? path : `/${path}`;
  const bases = [getBackendUrl(), LOCAL_THREATVISION];
  const seen = new Set<string>();
  let last: Response | null = null;

  for (const base of bases) {
    const root = base.replace(/\/$/, "");
    if (seen.has(root)) continue;
    seen.add(root);
    const url = `${root}${p}`;
    try {
      const res = await fetch(url, init);
      last = res;
      if (res.status !== 404) return res;
    } catch {
      continue;
    }
  }

  return (
    last ??
    new Response(JSON.stringify({ detail: "Cannot reach ThreatVision API. Start: uvicorn on 127.0.0.1:8001" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    })
  );
}

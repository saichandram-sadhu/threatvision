import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

function abortAfter(ms: number): AbortSignal {
  if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
    return AbortSignal.timeout(ms);
  }
  const c = new AbortController();
  setTimeout(() => c.abort(), ms);
  return c.signal;
}

type GeoOk = { ok: true; lat: number; lng: number };
type GeoNo = { ok: false };

function isValidPublicIpv4(ip: string): boolean {
  const m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(ip.trim());
  if (!m) return false;
  const o = [Number(m[1]), Number(m[2]), Number(m[3]), Number(m[4])];
  if (o.some((n) => n > 255 || n < 0)) return false;
  const [a, b] = o;
  if (a === 10 || a === 0 || a === 127) return false;
  if (a === 169 && b === 254) return false;
  if (a === 172 && b >= 16 && b <= 31) return false;
  if (a === 192 && b === 168) return false;
  if (a === 100 && b >= 64 && b <= 127) return false;
  return true;
}

async function fromIpWhoIs(ip: string): Promise<GeoOk | null> {
  const r = await fetch(`https://ipwho.is/${encodeURIComponent(ip)}`, {
    cache: "no-store",
    signal: abortAfter(12_000),
    headers: {
      Accept: "application/json",
      "User-Agent": "ThreatVision/1.0 (local geo map; server-side)",
    },
  });
  if (!r.ok) return null;
  const j = (await r.json()) as {
    success?: boolean;
    latitude?: number;
    longitude?: number;
  };
  if (j.success && typeof j.latitude === "number" && typeof j.longitude === "number") {
    return { ok: true, lat: j.latitude, lng: j.longitude };
  }
  return null;
}

async function fromIpApi(ip: string): Promise<GeoOk | null> {
  const r = await fetch(
    `http://ip-api.com/json/${encodeURIComponent(ip)}?fields=status,message,lat,lon`,
    {
      cache: "no-store",
      signal: abortAfter(12_000),
      headers: {
        Accept: "application/json",
        "User-Agent": "ThreatVision/1.0 (local geo map; server-side)",
      },
    },
  );
  if (!r.ok) return null;
  const j = (await r.json()) as { status?: string; lat?: number; lon?: number };
  if (j.status === "success" && typeof j.lat === "number" && typeof j.lon === "number") {
    return { ok: true, lat: j.lat, lng: j.lon };
  }
  return null;
}

/**
 * Server-side IP → lat/lng for the Analyze map. Avoids browser 403s from public geo APIs.
 */
export async function GET(request: NextRequest) {
  const ip = request.nextUrl.searchParams.get("ip")?.trim() ?? "";
  if (!ip || !isValidPublicIpv4(ip)) {
    return NextResponse.json({ ok: false } satisfies GeoNo);
  }

  try {
    const a = await fromIpWhoIs(ip);
    if (a) return NextResponse.json(a);
    const b = await fromIpApi(ip);
    if (b) return NextResponse.json(b);
  } catch {
    /* timeout / network */
  }

  return NextResponse.json({ ok: false } satisfies GeoNo);
}

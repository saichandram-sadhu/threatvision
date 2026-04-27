/** Same-origin server lookup — public geo APIs often 403 the browser. */
export async function lookupIpLatLng(ip: string): Promise<{ lat: number; lng: number } | null> {
  const trimmed = ip.trim();
  if (!trimmed) return null;
  try {
    const r = await fetch(`/api/geo/ip?ip=${encodeURIComponent(trimmed)}`, {
      cache: "no-store",
    });
    if (!r.ok) return null;
    const j = (await r.json()) as { ok?: boolean; lat?: number; lng?: number };
    if (j.ok && typeof j.lat === "number" && typeof j.lng === "number") {
      return { lat: j.lat, lng: j.lng };
    }
  } catch {
    /* ignore */
  }
  return null;
}

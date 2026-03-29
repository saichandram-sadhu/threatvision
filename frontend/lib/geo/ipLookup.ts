/** Client-side lookup (HTTPS) — visualization only. */
export async function lookupIpLatLng(ip: string): Promise<{ lat: number; lng: number } | null> {
  const trimmed = ip.trim();
  if (!trimmed) return null;
  try {
    const r = await fetch(`https://ipwho.is/${encodeURIComponent(trimmed)}`, {
      cache: "no-store",
    });
    if (!r.ok) return null;
    const j = (await r.json()) as {
      success?: boolean;
      latitude?: number;
      longitude?: number;
    };
    if (j.success && typeof j.latitude === "number" && typeof j.longitude === "number") {
      return { lat: j.latitude, lng: j.longitude };
    }
  } catch {
    /* ignore */
  }
  return null;
}

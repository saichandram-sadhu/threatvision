/**
 * Deterministic pseudo-coordinates for dashboard globe markers only (not real geo).
 */
export function hashIpToLatLng(ip: string): { lat: number; lng: number } {
  let h = 2166136261;
  for (let i = 0; i < ip.length; i++) {
    h ^= ip.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  const u = h >>> 0;
  const lat = (u % 18000) / 100 - 90;
  const lng = (((u / 18000) >>> 0) % 36000) / 100 - 180;
  return { lat, lng };
}

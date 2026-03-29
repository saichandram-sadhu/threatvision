import { formatRelativeIso } from "@/lib/format/relativeTime";
import type { MispFeedRow } from "@/lib/types/misp-explorer";

export function FeedsTable({ feeds }: { feeds: MispFeedRow[] }) {
  if (feeds.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-tv-border py-6 text-center text-sm text-tv-muted">
        No feeds returned from MISP.
      </p>
    );
  }

  const enabled = feeds.filter((f) => f.enabled).length;

  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-tv-surface/35 ring-1 ring-white/[0.04]">
      <div className="border-b border-tv-border px-4 py-3">
        <h3 className="font-display text-sm font-semibold text-tv-fg">Feeds</h3>
        <p className="text-xs text-tv-muted">
          {feeds.length} total — {enabled} enabled
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-tv-border bg-tv-void/40 text-xs uppercase tracking-wide text-tv-muted">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Format</th>
              <th className="px-4 py-2 font-medium">Last fetch</th>
              <th className="px-4 py-2 font-medium">Events</th>
              <th className="px-4 py-2 font-medium">Live sync</th>
            </tr>
          </thead>
          <tbody>
            {feeds.map((f, i) => (
              <tr key={f.id ?? `${f.name}-${i}`} className="border-b border-tv-border/60 last:border-0">
                <td className="max-w-[220px] truncate px-4 py-2.5 font-medium text-tv-fg" title={f.name ?? ""}>
                  {f.name ?? "—"}
                </td>
                <td className="px-4 py-2.5">
                  <span
                    className={
                      f.enabled
                        ? "rounded-full bg-threat-clean/15 px-2 py-0.5 text-xs font-medium text-threat-clean"
                        : "rounded-full bg-tv-muted/20 px-2 py-0.5 text-xs font-medium text-tv-muted"
                    }
                  >
                    {f.enabled ? "ON" : "OFF"}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-tv-muted">{f.source_format ?? "—"}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-tv-muted">
                  {formatRelativeIso(f.last_fetch)}
                </td>
                <td className="px-4 py-2.5 font-mono text-xs text-tv-cyan">
                  {f.event_count != null ? f.event_count.toLocaleString() : "—"}
                </td>
                <td className="px-4 py-2.5 text-tv-muted">{f.live_sync == null ? "—" : f.live_sync ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

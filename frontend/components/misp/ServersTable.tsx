import { formatRelativeIso } from "@/lib/format/relativeTime";
import type { MispServerRow } from "@/lib/types/misp-explorer";

function direction(s: MispServerRow): string {
  const p = s.push === true;
  const l = s.pull === true;
  if (p && l) return "Push / pull";
  if (p) return "Push";
  if (l) return "Pull";
  return "—";
}

export function ServersTable({ servers }: { servers: MispServerRow[] }) {
  if (servers.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-tv-border py-6 text-center text-sm text-tv-muted">
        No sync servers returned from MISP.
      </p>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-tv-surface/35 ring-1 ring-white/[0.04]">
      <div className="border-b border-tv-border px-4 py-3">
        <h3 className="font-display text-sm font-semibold text-tv-fg">Sync servers</h3>
        <p className="text-xs text-tv-muted">{servers.length} connection(s)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="border-b border-tv-border bg-tv-void/40 text-xs uppercase tracking-wide text-tv-muted">
            <tr>
              <th className="px-4 py-2 font-medium">Name</th>
              <th className="px-4 py-2 font-medium">URL</th>
              <th className="px-4 py-2 font-medium">Direction</th>
              <th className="px-4 py-2 font-medium">Last sync</th>
              <th className="px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {servers.map((s, i) => (
              <tr key={s.id ?? `${s.name}-${i}`} className="border-b border-tv-border/60 last:border-0">
                <td className="px-4 py-2.5 font-medium text-tv-fg">{s.name ?? "—"}</td>
                <td className="max-w-[200px] truncate px-4 py-2.5 text-xs text-tv-muted" title={s.url ?? ""}>
                  {s.url ?? "—"}
                </td>
                <td className="px-4 py-2.5 text-tv-muted">{direction(s)}</td>
                <td className="whitespace-nowrap px-4 py-2.5 text-tv-muted">
                  {formatRelativeIso(s.last_sync)}
                </td>
                <td className="px-4 py-2.5 text-xs capitalize text-tv-fg">{s.sync_status ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

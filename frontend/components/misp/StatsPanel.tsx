import type { MispStatsPanel as MispStats } from "@/lib/types/misp-explorer";

const cells: { key: keyof MispStats; label: string }[] = [
  { key: "total_events", label: "Events" },
  { key: "total_attributes", label: "Attributes" },
  { key: "total_objects", label: "Objects" },
  { key: "feeds_configured", label: "Feeds (configured)" },
  { key: "feeds_enabled", label: "Feeds (enabled)" },
  { key: "connected_servers", label: "Sync servers" },
  { key: "misp_version", label: "MISP version" },
];

export function StatsPanel({ stats }: { stats: MispStats }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-tv-surface/35 p-5 ring-1 ring-white/[0.04]">
      <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-tv-muted">
        Instance statistics
      </h3>
      <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cells.map(({ key, label }) => {
          const v = stats[key];
          const display =
            v === null || v === undefined
              ? "—"
              : typeof v === "number"
                ? v.toLocaleString()
                : String(v);
          return (
            <div key={key} className="rounded-lg border border-tv-border/80 bg-tv-void/40 px-3 py-2">
              <dt className="text-xs text-tv-muted">{label}</dt>
              <dd className="mt-0.5 font-mono text-sm text-tv-cyan">{display}</dd>
            </div>
          );
        })}
        <div className="rounded-lg border border-tv-border/80 bg-tv-void/40 px-3 py-2 sm:col-span-2 lg:col-span-3">
          <dt className="text-xs text-tv-muted">Last event added</dt>
          <dd className="mt-0.5 text-sm text-tv-fg">
            {stats.last_event_added
              ? new Date(stats.last_event_added).toLocaleString()
              : "—"}
          </dd>
        </div>
      </dl>
    </div>
  );
}

"use client";

import type { ActivityRecentItem } from "@/lib/types/dashboard";

function verdictClass(v: string): string {
  const u = v.toUpperCase();
  if (u === "MALICIOUS") return "text-threat-malicious border-threat-malicious/40 bg-threat-malicious/10";
  if (u === "SUSPICIOUS") return "text-threat-suspicious border-threat-suspicious/40 bg-threat-suspicious/10";
  if (u === "CLEAN") return "text-threat-clean border-threat-clean/30 bg-threat-clean/10";
  return "text-tv-muted border-tv-border bg-tv-void/50";
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ActivityFeed({
  items,
  loading,
  error,
}: {
  items: ActivityRecentItem[];
  loading: boolean;
  error: string | null;
}) {
  if (loading && items.length === 0) {
    return (
      <div className="dash-section rounded-xl border border-tv-border bg-tv-surface/60 p-6 backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">Recent activity</h2>
        <p className="mt-3 text-sm text-tv-muted">Loading…</p>
      </div>
    );
  }

  if (error && items.length === 0) {
    return (
      <div className="dash-section rounded-xl border border-tv-border bg-tv-surface/60 p-6 backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">Recent activity</h2>
        <p className="mt-3 text-sm text-threat-suspicious">{error}</p>
      </div>
    );
  }

  return (
    <div className="dash-section rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05] backdrop-blur-sm">
      <h2 className="font-display text-lg font-semibold text-tv-cyan">Recent activity</h2>
      <p className="mt-1 text-xs text-tv-muted">IOC analyses from the last sessions (flagged-by = malicious/suspicious sources).</p>
      <ul className="mt-4 max-h-[28rem] space-y-3 overflow-y-auto pr-1">
        {items.length === 0 ? (
          <li className="rounded-lg border border-dashed border-tv-border py-8 text-center text-sm text-tv-muted">
            No activity yet. Run a single-IOC analysis to populate this feed.
          </li>
        ) : (
          items.map((row) => (
            <li
              key={row.id}
              className="rounded-lg border border-tv-border bg-tv-void/40 px-4 py-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <code className="font-mono text-sm text-tv-fg">{row.ioc_snippet}</code>
                <time className="text-xs text-tv-muted" dateTime={row.created_at}>
                  {formatTime(row.created_at)}
                </time>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-md border px-2 py-0.5 text-xs font-medium uppercase ${verdictClass(row.verdict)}`}
                >
                  {row.verdict}
                </span>
                {row.flagged_by.length > 0 && (
                  <>
                    <span className="text-xs text-tv-muted">Flagged by:</span>
                    {row.flagged_by.map((c) => (
                      <span
                        key={c.id}
                        className="inline-flex items-center rounded-full border border-tv-purple/40 bg-tv-purple/15 px-2 py-0.5 text-[11px] text-tv-accent"
                      >
                        {c.display_name}
                      </span>
                    ))}
                  </>
                )}
              </div>
            </li>
          ))
        )}
      </ul>
    </div>
  );
}

"use client";

import type { VerdictBucket } from "@/lib/types/dashboard";

function barColor(verdict: string): string {
  const u = verdict.toUpperCase();
  if (u === "MALICIOUS") return "bg-threat-malicious";
  if (u === "SUSPICIOUS") return "bg-threat-suspicious";
  if (u === "CLEAN") return "bg-threat-clean";
  return "bg-tv-muted";
}

export function VerdictDistribution({
  buckets,
  loading,
}: {
  buckets: VerdictBucket[];
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="dash-section h-36 animate-pulse rounded-xl border border-tv-border bg-tv-surface/50" />
    );
  }

  const max = Math.max(1, ...buckets.map((b) => b.count));

  if (buckets.length === 0) {
    return (
      <div className="dash-section rounded-xl border border-tv-border bg-tv-surface/40 p-5 backdrop-blur-sm">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-tv-muted">
          Verdict mix (30d)
        </h2>
        <p className="mt-3 text-sm text-tv-muted">No analyses in the last 30 days.</p>
      </div>
    );
  }

  return (
    <div className="dash-section rounded-xl border border-white/[0.08] bg-tv-surface/35 p-5 ring-1 ring-white/[0.04] backdrop-blur-sm">
      <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-tv-muted">
        Verdict mix (30d)
      </h2>
      <ul className="mt-4 space-y-3">
        {buckets.map((b) => (
          <li key={b.verdict}>
            <div className="flex justify-between text-xs">
              <span className="font-medium text-tv-fg">{b.verdict}</span>
              <span className="tabular-nums text-tv-muted">{b.count.toLocaleString()}</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-tv-void">
              <div
                className={`h-full rounded-full transition-all ${barColor(b.verdict)}`}
                style={{ width: `${(b.count / max) * 100}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

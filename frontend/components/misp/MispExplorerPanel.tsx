"use client";

import Link from "next/link";

import { FeedsTable } from "@/components/misp/FeedsTable";
import { ServersTable } from "@/components/misp/ServersTable";
import { StatsPanel } from "@/components/misp/StatsPanel";
import { SyncIndicator } from "@/components/misp/SyncIndicator";
import { TaxonomiesList } from "@/components/misp/TaxonomiesList";
import { useMispExplorer } from "@/lib/hooks/useMispExplorer";

export function MispExplorerPanel({
  enabled,
  compact,
}: {
  enabled: boolean;
  /** Fewer sections / tighter spacing on integrations page */
  compact?: boolean;
}) {
  const { data, error, loading, refetch } = useMispExplorer(enabled);

  if (!enabled) {
    return null;
  }

  if (loading && !data) {
    return (
      <div className="rounded-xl border border-tv-border bg-tv-surface/40 p-8 text-center text-sm text-tv-muted">
        Loading MISP explorer…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-threat-suspicious/40 bg-threat-suspicious/10 p-6 text-sm text-threat-suspicious">
        {error}
      </div>
    );
  }

  if (!data) return null;

  const errs = Object.entries(data.source_errors || {});
  const feedSlice = compact ? data.feeds.slice(0, 8) : data.feeds;

  return (
    <div className={compact ? "space-y-4" : "space-y-6"}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold text-tv-fg">MISP Instance Explorer</h3>
          <p className="mt-1 text-xs text-tv-muted">
            Refreshes every 30s · Resolution: {data.resolution}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void refetch()}
          className="rounded-lg border border-tv-border px-3 py-1.5 text-xs text-tv-muted hover:border-tv-cyan hover:text-tv-cyan"
        >
          Refresh now
        </button>
      </div>

      <div className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-5 ring-1 ring-white/[0.05]">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-tv-muted">Connection</h4>
        <p className="mt-2 font-mono text-sm text-tv-fg">{data.base_url}</p>
        <div className="mt-3 flex flex-wrap gap-4 text-sm">
          <span className={data.connected ? "text-threat-clean" : "text-threat-malicious"}>
            {data.connected ? "Connected" : "Disconnected"}
          </span>
          <span className="text-tv-muted">Version: {data.misp_version ?? "—"}</span>
          <span className="text-tv-cyan">
            Events: {data.stats.total_events != null ? data.stats.total_events.toLocaleString() : "—"}
          </span>
        </div>
      </div>

      <SyncIndicator syncIndicator={data.sync_indicator} fetchedAt={data.fetched_at} />

      {errs.length > 0 && (
        <div className="rounded-lg border border-threat-suspicious/35 bg-threat-suspicious/10 p-4 text-xs text-threat-suspicious">
          <p className="font-medium">Source warnings</p>
          <ul className="mt-2 list-inside list-disc">
            {errs.map(([k, v]) => (
              <li key={k}>
                {k}: {v}
              </li>
            ))}
          </ul>
        </div>
      )}

      <StatsPanel stats={data.stats} />
      <FeedsTable feeds={feedSlice} />
      {!compact && (
        <>
          <ServersTable servers={data.servers} />
          <TaxonomiesList taxonomies={data.taxonomies} />
        </>
      )}
      {compact && data.feeds.length > 8 && (
        <p className="text-center text-xs text-tv-muted">
          Showing 8 of {data.feeds.length} feeds. Open{" "}
          <Link href="/settings/misp" className="text-tv-cyan hover:underline">
            MISP explorer
          </Link>{" "}
          for the full list.
        </p>
      )}
    </div>
  );
}

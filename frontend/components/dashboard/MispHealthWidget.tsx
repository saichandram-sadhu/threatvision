"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type ExplorerJson = {
  connected: boolean;
  base_url: string;
  resolution?: string;
  sync_indicator: string;
  fetched_at: string;
  stats: {
    total_events: number | null;
    feeds_enabled: number | null;
    feeds_configured: number | null;
  };
  feeds: { last_fetch: string | null }[];
  servers: { last_sync: string | null }[];
};

function collectSyncDates(data: ExplorerJson): string[] {
  const out: string[] = [];
  for (const f of data.feeds) {
    if (f.last_fetch) out.push(f.last_fetch);
  }
  for (const s of data.servers) {
    if (s.last_sync) out.push(s.last_sync);
  }
  return out;
}

function latestIso(dates: string[]): string | null {
  let best: number | null = null;
  let out: string | null = null;
  for (const d of dates) {
    const t = Date.parse(d);
    if (!Number.isNaN(t) && (best === null || t > best)) {
      best = t;
      out = d;
    }
  }
  return out;
}

function formatRelative(iso: string | null): string {
  if (!iso) return "—";
  const diffSec = (Date.parse(iso) - Date.now()) / 1000;
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const abs = Math.abs(diffSec);
  if (abs < 45) return rtf.format(Math.round(diffSec), "second");
  if (abs < 3600) return rtf.format(Math.round(diffSec / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(diffSec / 3600), "hour");
  return rtf.format(Math.round(diffSec / 86400), "day");
}

type WidgetState =
  | { kind: "loading" }
  | { kind: "disconnected"; message: string }
  | { kind: "error"; message: string }
  | { kind: "ok"; data: ExplorerJson };

export function MispHealthWidget({ enabled }: { enabled: boolean }) {
  const [state, setState] = useState<WidgetState>(() =>
    enabled
      ? { kind: "loading" }
      : { kind: "disconnected", message: "Sign in with email/password to load MISP status." },
  );

  const load = useCallback(async () => {
    if (!enabled) {
      setState({ kind: "disconnected", message: "Sign in with email/password to load MISP status." });
      return;
    }
    try {
      const res = await fetch("/api/threatvision/misp/explorer", { credentials: "include" });
      if (res.status === 400) {
        const j = (await res.json().catch(() => ({}))) as { detail?: string };
        setState({
          kind: "disconnected",
          message: typeof j.detail === "string" ? j.detail : "MISP is not configured.",
        });
        return;
      }
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string };
        setState({
          kind: "error",
          message: j.message || `Explorer request failed (${res.status})`,
        });
        return;
      }
      const data = (await res.json()) as ExplorerJson;
      setState({ kind: "ok", data });
    } catch (e) {
      setState({
        kind: "error",
        message: e instanceof Error ? e.message : "Network error",
      });
    }
  }, [enabled]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!enabled) return;
    const t = window.setInterval(() => void load(), 30_000);
    return () => window.clearInterval(t);
  }, [enabled, load]);

  if (state.kind === "loading") {
    return (
      <div className="dash-section rounded-xl border border-tv-border bg-tv-surface/60 p-6 backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-purple">MISP health</h2>
        <p className="mt-3 text-sm text-tv-muted">Loading explorer snapshot…</p>
      </div>
    );
  }

  if (state.kind === "disconnected") {
    return (
      <div className="dash-section rounded-xl border border-tv-border bg-tv-surface/60 p-6 backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-purple">MISP health</h2>
        <p className="mt-3 text-sm text-tv-muted">{state.message}</p>
        <Link
          href="/settings"
          className="mt-4 inline-block text-sm font-medium text-tv-cyan hover:underline"
        >
          Open settings
        </Link>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="dash-section rounded-xl border border-threat-suspicious/40 bg-tv-surface/60 p-6 backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-purple">MISP health</h2>
        <p className="mt-3 text-sm text-threat-suspicious">{state.message}</p>
      </div>
    );
  }

  const { data } = state;
  const feedsCfg = data.stats.feeds_configured ?? 0;
  const feedsEn = data.stats.feeds_enabled ?? 0;
  const feedsDisabled = Math.max(0, feedsCfg - feedsEn);
  const lastSync = formatRelative(latestIso(collectSyncDates(data)));
  const ind = data.sync_indicator;

  return (
    <div className="dash-section rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05] backdrop-blur-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold text-tv-purple">MISP health</h2>
          <p className="mt-1 truncate text-xs text-tv-muted" title={data.base_url}>
            {data.base_url}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={
              ind === "error"
                ? "h-2 w-2 rounded-full bg-threat-malicious"
                : ind === "syncing"
                  ? "h-2 w-2 animate-pulse rounded-full bg-threat-clean"
                  : "h-2 w-2 rounded-full bg-tv-muted"
            }
            aria-hidden
          />
          <span className="text-xs capitalize text-tv-muted">{ind}</span>
        </div>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-tv-muted">Status</dt>
          <dd className="font-medium text-tv-fg">{data.connected ? "Connected" : "Disconnected"}</dd>
        </div>
        <div>
          <dt className="text-tv-muted">Total events</dt>
          <dd className="font-mono text-tv-cyan">
            {data.stats.total_events != null ? data.stats.total_events.toLocaleString() : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-tv-muted">Feeds</dt>
          <dd className="text-tv-fg">
            <span className="text-threat-clean">{feedsEn} active</span>
            {feedsCfg > 0 && (
              <>
                , <span className="text-tv-muted">{feedsDisabled} disabled</span>
              </>
            )}
          </dd>
        </div>
        <div>
          <dt className="text-tv-muted">Last sync signal</dt>
          <dd className="text-tv-fg">{lastSync}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-tv-muted">
        Snapshot {formatRelative(data.fetched_at)} · Refreshes every 30s
      </p>
      <Link
        href="/settings/misp"
        className="mt-3 inline-block text-sm font-medium text-tv-cyan hover:underline"
      >
        Open MISP explorer →
      </Link>
    </div>
  );
}

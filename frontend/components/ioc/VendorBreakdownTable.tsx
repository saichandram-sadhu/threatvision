"use client";

import { useMemo, useState } from "react";

import { SOURCE_CATALOG_IDS } from "@/lib/ioc/catalogOrder";
import type { MispEventInfo, SourceResult } from "@/lib/types/analyze";

function orderSources(sources: SourceResult[]): SourceResult[] {
  const byId = new Map(sources.map((s) => [s.id, s]));
  const out: SourceResult[] = [];
  for (const id of SOURCE_CATALOG_IDS) {
    const row = byId.get(id);
    if (row) out.push(row);
  }
  const catalog = new Set<string>(SOURCE_CATALOG_IDS);
  for (const s of sources) {
    if (!catalog.has(s.id)) {
      out.push(s);
    }
  }
  return out;
}

function parseMispEvents(metadata: Record<string, unknown>): MispEventInfo[] {
  const raw = metadata.events;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((x) => {
      if (!x || typeof x !== "object") return null;
      const o = x as Record<string, unknown>;
      const eventId = String(o.eventId ?? o.event_id ?? "");
      if (!eventId) return null;
      return {
        eventId,
        eventName: String(o.eventName ?? o.event_name ?? ""),
        tags: Array.isArray(o.tags) ? o.tags.map(String) : [],
        tlp: String(o.tlp ?? "unknown"),
        feedName: o.feedName != null ? String(o.feedName) : o.feed_name != null ? String(o.feed_name) : null,
      };
    })
    .filter((x): x is MispEventInfo => x !== null);
}

function rowShellClass(status: SourceResult["status"]): string {
  if (status === "not_configured") {
    return "border-tv-border/60 bg-tv-void/30 opacity-80";
  }
  if (status === "unavailable") {
    return "border-threat-suspicious/45 bg-threat-suspicious/10";
  }
  return "border-white/[0.08] bg-tv-surface/25";
}

function verdictBadge(verdict: string | null | undefined, status: SourceResult["status"]): string {
  if (status !== "ok") return "text-tv-muted";
  const v = (verdict || "unknown").toLowerCase();
  if (v === "malicious") return "text-threat-malicious";
  if (v === "suspicious") return "text-threat-suspicious";
  if (v === "clean") return "text-threat-clean";
  return "text-tv-muted";
}

export function VendorBreakdownTable({ sources }: { sources: SourceResult[] }) {
  const rows = useMemo(() => orderSources(sources), [sources]);
  const [mispOpen, setMispOpen] = useState(false);

  return (
    <div className="overflow-hidden rounded-xl border border-white/[0.08] ring-1 ring-white/[0.04]">
      <div className="border-b border-tv-border bg-tv-void/50 px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-tv-muted">
          Vendor breakdown
        </h2>
        <p className="mt-1 text-xs text-tv-muted">Fixed catalog order (spec §4.4). Primary transparency surface.</p>
      </div>
      <div className="divide-y divide-tv-border/60">
        {rows.map((s) => {
          const isMisp = s.id === "misp";
          const events = isMisp ? parseMispEvents(s.metadata) : [];
          const expandable = isMisp && events.length > 0 && s.status === "ok";

          return (
            <div key={s.id} className={`border-l-2 border-l-transparent px-4 py-3 ${rowShellClass(s.status)}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-tv-fg">{s.displayName}</span>
                    <span className="rounded bg-tv-void/80 px-1.5 py-0.5 font-mono text-[10px] text-tv-muted">
                      {s.status}
                    </span>
                    {s.errorCode && (
                      <span className="text-[10px] text-threat-suspicious">{s.errorCode}</span>
                    )}
                  </div>
                  <ul className="mt-2 space-y-1 text-sm text-tv-muted">
                    {(s.detailLines || []).slice(0, 8).map((line, i) => (
                      <li key={i} className="leading-snug">
                        {line}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="shrink-0 text-right">
                  <span
                    className={`text-sm font-semibold uppercase ${verdictBadge(s.verdict, s.status)}`}
                  >
                    {s.status === "ok" ? s.verdict ?? "unknown" : "—"}
                  </span>
                  {expandable && (
                    <button
                      type="button"
                      onClick={() => setMispOpen((v) => !v)}
                      className="mt-2 block w-full rounded-md border border-tv-border px-2 py-1 text-xs text-tv-cyan hover:border-tv-cyan"
                    >
                      {mispOpen ? "Hide events" : `Events (${events.length})`}
                    </button>
                  )}
                </div>
              </div>
              {expandable && mispOpen && (
                <div className="mt-4 overflow-x-auto rounded-lg border border-tv-border bg-tv-void/50">
                  <table className="w-full min-w-[520px] text-left text-xs">
                    <thead className="border-b border-tv-border text-tv-muted">
                      <tr>
                        <th className="px-3 py-2 font-medium">Event</th>
                        <th className="px-3 py-2 font-medium">Name</th>
                        <th className="px-3 py-2 font-medium">TLP</th>
                        <th className="px-3 py-2 font-medium">Feed / source</th>
                        <th className="px-3 py-2 font-medium">Tags</th>
                      </tr>
                    </thead>
                    <tbody>
                      {events.map((e) => (
                        <tr key={e.eventId} className="border-b border-tv-border/50 last:border-0">
                          <td className="whitespace-nowrap px-3 py-2 font-mono text-tv-cyan">{e.eventId}</td>
                          <td className="max-w-[200px] truncate px-3 py-2 text-tv-fg" title={e.eventName}>
                            {e.eventName || "—"}
                          </td>
                          <td className="px-3 py-2 text-tv-muted">{e.tlp}</td>
                          <td className="max-w-[180px] truncate px-3 py-2 text-tv-muted" title={e.feedName ?? ""}>
                            {e.feedName ?? "—"}
                          </td>
                          <td className="max-w-[240px] truncate px-3 py-2 text-tv-muted" title={e.tags.join(", ")}>
                            {e.tags.length ? e.tags.join(", ") : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

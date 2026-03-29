"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";

import { ConfidenceGauge } from "@/components/ioc/ConfidenceGauge";
import { VendorBreakdownTable } from "@/components/ioc/VendorBreakdownTable";
import { lookupIpLatLng } from "@/lib/geo/ipLookup";
import type { AnalyzeResponse } from "@/lib/types/analyze";

const IocIpMap = dynamic(() => import("@/components/ioc/IocIpMap").then((m) => m.IocIpMap), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse rounded-xl bg-tv-surface/50" />,
});

export function AnalyzePageClient() {
  const [q, setQ] = useState("");
  const [pending, setPending] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [geo, setGeo] = useState<{ lat: number; lng: number } | null>(null);
  const [geoErr, setGeoErr] = useState<string | null>(null);

  const run = useCallback(async () => {
    const ioc = q.trim();
    if (!ioc) return;
    setErr(null);
    setResult(null);
    setGeo(null);
    setGeoErr(null);
    setPending(true);
    try {
      const res = await fetch("/api/threatvision/ioc/analyze", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ioc }),
      });
      const data = (await res.json().catch(() => ({}))) as AnalyzeResponse & {
        detail?: unknown;
        message?: string;
      };
      if (!res.ok) {
        const d = data.detail;
        let msg = data.message || `Analyze failed (${res.status})`;
        if (typeof d === "string") msg = d;
        else if (Array.isArray(d) && d[0] && typeof d[0] === "object" && d[0] !== null && "msg" in d[0]) {
          msg = String((d[0] as { msg: unknown }).msg);
        }
        setErr(msg);
        return;
      }
      setResult(data as AnalyzeResponse);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    } finally {
      setPending(false);
    }
  }, [q]);

  useEffect(() => {
    if (!result || result.ioc.type !== "ip") {
      setGeo(null);
      return;
    }
    let cancelled = false;
    setGeoErr(null);
    void (async () => {
      const loc = await lookupIpLatLng(result.ioc.normalized);
      if (cancelled) return;
      if (loc) setGeo(loc);
      else setGeoErr("Could not resolve IP location for map.");
    })();
    return () => {
      cancelled = true;
    };
  }, [result]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Analyze IOC</h1>
        <p className="mt-2 max-w-2xl text-sm text-tv-muted">
          Single-indicator run through MISP and configured enrichers. Vendor table stays in catalog order (§4.4).
        </p>
      </div>

      <form
        className="flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={(e) => {
          e.preventDefault();
          void run();
        }}
      >
        <div className="min-w-0 flex-1">
          <label htmlFor="ioc-q" className="block text-sm text-tv-muted">
            Indicator
          </label>
          <input
            id="ioc-q"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2.5 font-mono text-sm text-tv-fg outline-none focus:border-tv-cyan/60 focus:ring-2 focus:ring-tv-cyan/30"
            placeholder="IP, domain, hash, URL…"
            autoComplete="off"
          />
        </div>
        <button
          type="submit"
          disabled={pending || !q.trim()}
          className="rounded-lg bg-tv-cyan px-6 py-2.5 font-medium text-tv-void shadow-lg shadow-tv-cyan/15 hover:opacity-95 disabled:opacity-50"
        >
          {pending ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      {err && (
        <div className="rounded-lg border border-threat-malicious/40 bg-threat-malicious/10 px-4 py-3 text-sm text-threat-malicious">
          {err}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-start">
            <div className="rounded-xl border border-white/[0.08] bg-tv-surface/35 p-6 ring-1 ring-white/[0.04]">
              <p className="text-xs uppercase tracking-wide text-tv-muted">IOC</p>
              <p className="mt-1 font-mono text-lg text-tv-cyan">{result.ioc.normalized}</p>
              <p className="mt-2 text-sm text-tv-muted">
                Type <span className="font-mono text-tv-fg">{result.ioc.type}</span> · Raw length{" "}
                {result.ioc.raw.length}
              </p>
              {result.aggregate.rationale && (
                <p className="mt-4 border-t border-tv-border pt-4 text-sm text-tv-muted">
                  {result.aggregate.rationale}
                </p>
              )}
            </div>
            <div className="flex flex-col items-center justify-center rounded-xl border border-white/[0.08] bg-tv-surface/35 p-6 ring-1 ring-white/[0.04]">
              <p className="text-xs uppercase tracking-wide text-tv-muted">Aggregate</p>
              <p
                className={`mt-2 font-display text-2xl font-bold ${
                  result.aggregate.verdict === "MALICIOUS"
                    ? "text-threat-malicious"
                    : result.aggregate.verdict === "SUSPICIOUS"
                      ? "text-threat-suspicious"
                      : "text-threat-clean"
                }`}
              >
                {result.aggregate.verdict}
              </p>
              <ConfidenceGauge verdict={result.aggregate.verdict} confidence={result.aggregate.confidence} />
            </div>
          </div>

          <VendorBreakdownTable sources={result.sources} />

          {result.ioc.type === "ip" && (
            <section>
              <h2 className="font-display text-lg font-semibold text-tv-fg">Map</h2>
              <p className="mt-1 text-xs text-tv-muted">
                Approximate location via ipwho.is (HTTPS). Not a forensic guarantee.
              </p>
              <div className="mt-3 overflow-hidden rounded-xl border border-tv-border">
                {geo && <IocIpMap lat={geo.lat} lng={geo.lng} label={result.ioc.normalized} />}
                {!geo && !geoErr && <div className="h-64 animate-pulse bg-tv-surface/50" />}
                {geoErr && (
                  <div className="flex h-64 items-center justify-center text-sm text-tv-muted">{geoErr}</div>
                )}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

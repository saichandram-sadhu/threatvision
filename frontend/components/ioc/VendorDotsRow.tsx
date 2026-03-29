"use client";

import { SOURCE_CATALOG_IDS } from "@/lib/ioc/catalogOrder";
import type { SourceResult } from "@/lib/types/analyze";

function dotStyle(s: SourceResult | undefined): { bg: string; ring: string; title: string } {
  if (!s) {
    return { bg: "bg-tv-border", ring: "", title: "Missing row" };
  }
  if (s.status === "not_configured") {
    return { bg: "bg-tv-muted/40", ring: "ring-1 ring-tv-border", title: `${s.displayName}: not configured` };
  }
  if (s.status === "unavailable") {
    return {
      bg: "bg-threat-suspicious/30",
      ring: "ring-2 ring-threat-suspicious",
      title: `${s.displayName}: unavailable${s.errorCode ? ` (${s.errorCode})` : ""}`,
    };
  }
  const v = (s.verdict || "unknown").toLowerCase();
  if (v === "malicious") {
    return { bg: "bg-threat-malicious", ring: "", title: `${s.displayName}: malicious` };
  }
  if (v === "suspicious") {
    return { bg: "bg-threat-suspicious", ring: "", title: `${s.displayName}: suspicious` };
  }
  if (v === "clean") {
    return { bg: "bg-threat-clean", ring: "", title: `${s.displayName}: clean` };
  }
  return { bg: "bg-tv-muted/50", ring: "", title: `${s.displayName}: unknown` };
}

export function VendorDotsRow({ sources }: { sources: SourceResult[] }) {
  const byId = new Map(sources.map((x) => [x.id, x]));

  return (
    <div className="flex flex-wrap items-center gap-1.5" role="list" aria-label="Vendor verdict dots">
      {SOURCE_CATALOG_IDS.map((id) => {
        const s = byId.get(id);
        const { bg, ring, title } = dotStyle(s);
        const line = s?.detailLines?.[0];
        const tip = line ? `${title}\n${line}` : title;
        return (
          <span
            key={id}
            role="listitem"
            title={tip}
            className={`inline-block h-2.5 w-2.5 rounded-full ${bg} ${ring}`}
          />
        );
      })}
    </div>
  );
}

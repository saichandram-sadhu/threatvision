"use client";

import type { AggregateVerdict } from "@/lib/types/analyze";

function accentClass(v: AggregateVerdict): string {
  if (v === "MALICIOUS") return "text-threat-malicious";
  if (v === "SUSPICIOUS") return "text-threat-suspicious";
  return "text-threat-clean";
}

/** Semicircle progress for aggregate confidence (0–100). */
export function ConfidenceGauge({
  verdict,
  confidence,
}: {
  verdict: AggregateVerdict;
  confidence: number;
}) {
  const pct = Math.max(0, Math.min(100, Math.round(confidence)));
  const arc = (pct / 100) * 126;
  const cls = accentClass(verdict);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative h-[5.5rem] w-36">
        <svg viewBox="0 0 100 58" className="h-full w-full" aria-hidden>
          <path
            d="M 12 48 A 38 38 0 0 1 88 48"
            fill="none"
            stroke="currentColor"
            strokeWidth="7"
            strokeLinecap="round"
            className="text-tv-border"
          />
          <path
            d="M 12 48 A 38 38 0 0 1 88 48"
            fill="none"
            stroke="currentColor"
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={`${arc} 126`}
            className={cls}
          />
        </svg>
        <div className="absolute bottom-0 left-0 right-0 text-center">
          <span className={`font-display text-3xl font-bold tabular-nums ${cls}`}>{pct}</span>
        </div>
      </div>
      <p className="text-[11px] uppercase tracking-wide text-tv-muted">Confidence</p>
    </div>
  );
}

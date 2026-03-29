"use client";

import { useReducedMotion } from "framer-motion";
import { gsap } from "gsap";
import { useEffect, useRef } from "react";

function StatCounter({
  value,
  label,
  sub,
}: {
  value: number;
  label: string;
  sub?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduced) {
      el.textContent = value.toLocaleString();
      return;
    }
    const o = { n: 0 };
    const anim = gsap.to(o, {
      n: value,
      duration: 1.05,
      ease: "power2.out",
      onUpdate: () => {
        el.textContent = Math.round(o.n).toLocaleString();
      },
    });
    return () => {
      anim.kill();
    };
  }, [value, reduced]);

  return (
    <div className="rounded-xl border border-white/[0.08] bg-tv-surface/35 p-4 ring-1 ring-white/[0.04] backdrop-blur-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-tv-muted">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold tabular-nums text-tv-cyan">
        <span ref={ref}>0</span>
      </p>
      {sub && <p className="mt-0.5 text-[11px] text-tv-muted">{sub}</p>}
    </div>
  );
}

export function DashboardStatsStrip({
  stats,
  loading,
  error,
}: {
  stats: {
    analyses_1d: number;
    analyses_7d: number;
    analyses_30d: number;
    analyses_all: number;
  } | null;
  loading: boolean;
  error: string | null;
}) {
  if (error && !stats) {
    return (
      <div className="dash-section rounded-xl border border-threat-suspicious/35 bg-tv-surface/40 p-4 text-sm text-threat-suspicious">
        {error}
      </div>
    );
  }

  if (loading && !stats) {
    return (
      <div className="dash-section grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-24 animate-pulse rounded-xl border border-tv-border bg-tv-surface/50"
          />
        ))}
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="dash-section grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <StatCounter value={stats.analyses_1d} label="24 hours" sub="Analyses logged" />
      <StatCounter value={stats.analyses_7d} label="7 days" />
      <StatCounter value={stats.analyses_30d} label="30 days" />
      <StatCounter value={stats.analyses_all} label="All time" />
    </div>
  );
}

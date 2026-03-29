"use client";

import dynamic from "next/dynamic";
import { useReducedMotion } from "framer-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useLayoutEffect } from "react";

import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { DashboardStatsStrip } from "@/components/dashboard/DashboardStatsStrip";
import { MispHealthWidget } from "@/components/dashboard/MispHealthWidget";
import { VerdictDistribution } from "@/components/dashboard/VerdictDistribution";
import { useActivityRecent } from "@/lib/hooks/useActivityRecent";
import { useDashboardStats } from "@/lib/hooks/useDashboardStats";

const ThreatGlobe = dynamic(
  () => import("@/components/dashboard/ThreatGlobe").then((m) => m.ThreatGlobe),
  { ssr: false, loading: () => <div className="h-64 animate-pulse rounded-xl bg-tv-surface/50" /> },
);

type Props = {
  apiEnabled: boolean;
  email: string | null;
  role: string | null;
};

export function DashboardClient({ apiEnabled, email, role }: Props) {
  const reduceMotion = useReducedMotion();
  const statsQ = useDashboardStats(apiEnabled);
  const activityQ = useActivityRecent(apiEnabled);

  useLayoutEffect(() => {
    if (reduceMotion) return;
    gsap.registerPlugin(ScrollTrigger);
    const ctx = gsap.context(() => {
      gsap.utils.toArray<HTMLElement>(".dash-section").forEach((el) => {
        gsap.from(el, {
          opacity: 0,
          y: 22,
          duration: 0.62,
          ease: "power2.out",
          scrollTrigger: {
            trigger: el,
            start: "top 92%",
            once: true,
          },
        });
      });
    });
    return () => ctx.revert();
  }, [reduceMotion]);

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Dashboard</h1>
        <p className="max-w-2xl text-tv-muted">
          Live snapshot of your IOC analyses, MISP instance health, and recent verdicts. Stats refresh every minute;
          MISP explorer every 30 seconds.
        </p>
        {!apiEnabled && (
          <p className="rounded-lg border border-threat-suspicious/40 bg-threat-suspicious/10 px-4 py-3 text-sm text-threat-suspicious">
            API-backed widgets are disabled for this session. Sign in with <strong>email and password</strong> so your
            account links to ThreatVision and the BFF can reach FastAPI.
          </p>
        )}
        <dl className="flex flex-wrap gap-4 text-sm">
          <div>
            <dt className="text-tv-muted">Email</dt>
            <dd className="font-mono text-tv-fg">{email ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-tv-muted">Role</dt>
            <dd>{role ?? "—"}</dd>
          </div>
        </dl>
      </header>

      <DashboardStatsStrip
        stats={statsQ.data}
        loading={statsQ.loading}
        error={statsQ.error}
      />

      <VerdictDistribution
        buckets={statsQ.data?.verdict_distribution_30d ?? []}
        loading={statsQ.loading && !statsQ.data}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <MispHealthWidget enabled={apiEnabled} />
        <ActivityFeed
          items={activityQ.data?.items ?? []}
          loading={activityQ.loading}
          error={activityQ.error}
        />
      </div>

      <section className="dash-section space-y-3">
        <h2 className="font-display text-lg font-semibold text-tv-fg">Threat globe</h2>
        <p className="text-xs text-tv-muted">
          Dots use deterministic positions from IPv4 snippets in your 30-day activity (visualization aid, not
          geolocation).
        </p>
        <ThreatGlobe topIps={statsQ.data?.top_ips_30d ?? []} />
      </section>
    </div>
  );
}

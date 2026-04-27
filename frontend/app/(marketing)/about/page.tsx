import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — ThreatVision",
  description: "Mission, architecture, and open-source stack for ThreatVision.",
};

export default function AboutPage() {
  return (
    <article className="max-w-none space-y-10">
      <div>
        <h1 className="font-display text-4xl font-bold text-tv-fg">About ThreatVision</h1>
        <p className="mt-4 text-lg text-tv-muted">
          ThreatVision is an IOC analysis and threat intelligence web platform: VirusTotal-style{" "}
          <strong className="text-tv-fg">per-vendor transparency</strong>, with{" "}
          <strong className="text-tv-fg">MISP</strong> as the primary intelligence source and optional external
          enrichers.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="font-display text-2xl font-semibold text-tv-cyan">Mission</h2>
        <p className="text-tv-muted">
          Every analysis exposes a <strong className="text-tv-fg">fixed vendor catalog</strong> — same order in the
          UI, exports, and API — so analysts see who said what, not a single black-box score. MISP instance discovery
          (feeds, sync partners, taxonomies) is a first-class differentiator.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-2xl font-semibold text-tv-cyan">Architecture (logical)</h2>
        <pre className="overflow-x-auto rounded-xl border border-tv-border bg-tv-surface/50 p-4 font-mono text-xs text-tv-muted leading-relaxed">
          {`┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐
│   Browser   │────▶│  Next.js BFF │────▶│   FastAPI   │────▶│  MISP +  │
│  (session)  │◀────│  (session +  │◀────│ (internal   │◀────│ enrichers│
└─────────────┘     │ internal JWT)│     │  JWT, DB)   │     └──────────┘
                      └──────────────┘     └─────────────┘
                             │                    │
                             │                    └── PostgreSQL (encrypted secrets, activity, jobs)
                             └── NextAuth (credentials / OAuth)`}
        </pre>
        <p className="text-sm text-tv-muted">
          Programmatic clients may use a per-user API key; the dashboard is optimized for browser sessions through the
          BFF.
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-2xl font-semibold text-tv-purple">Stack</h2>
        <ul className="list-inside list-disc space-y-2 text-tv-muted">
          <li>
            <strong className="text-tv-fg">Frontend:</strong> Next.js 14 (App Router), TypeScript, Tailwind, React Three
            Fiber, GSAP, Leaflet, NextAuth
          </li>
          <li>
            <strong className="text-tv-fg">Backend:</strong> FastAPI, asyncpg, Fernet-at-rest for integration secrets
          </li>
          <li>
            <strong className="text-tv-fg">Data:</strong> PostgreSQL (users, activity, bulk jobs, rate limits)
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-2xl font-semibold text-tv-purple">Documentation</h2>
        <p className="text-tv-muted">
          SIEM integration references live in the repository under{" "}
          <code className="rounded bg-tv-surface px-1.5 py-0.5 font-mono text-sm text-tv-cyan">docs/integrations/</code>{" "}
          (e.g. generic webhooks and Wazuh-oriented notes).
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="font-display text-2xl font-semibold text-tv-purple">Credits &amp; OSS</h2>
        <p className="text-tv-muted">
          ThreatVision builds on outstanding open-source projects including{" "}
          <strong className="text-tv-fg">Next.js</strong>, <strong className="text-tv-fg">React</strong>,{" "}
          <strong className="text-tv-fg">FastAPI</strong>, <strong className="text-tv-fg">PostgreSQL</strong>,{" "}
          <strong className="text-tv-fg">Three.js</strong>, <strong className="text-tv-fg">Leaflet</strong>,{" "}
          <strong className="text-tv-fg">OpenStreetMap</strong> tiles, and the broader Python and TypeScript ecosystems.
          Respect each project&apos;s license when redistributing or modifying components.
        </p>
      </section>
    </article>
  );
}

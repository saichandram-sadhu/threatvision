import Link from "next/link";

export default function SettingsIndexPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Settings</h1>
        <p className="mt-2 max-w-2xl text-tv-muted">
          Manage MISP connectivity, vendor API keys, and explore your connected MISP instance.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/settings/integrations"
          className="group rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05] transition hover:border-tv-cyan/40 hover:ring-tv-cyan/20"
        >
          <h2 className="font-display text-lg font-semibold text-tv-cyan group-hover:underline">Integrations</h2>
          <p className="mt-2 text-sm text-tv-muted">
            MISP URL &amp; key, per-source toggles and API keys, test connections, and a compact explorer preview.
          </p>
        </Link>
        <Link
          href="/settings/misp"
          className="group rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05] transition hover:border-tv-purple/40 hover:ring-tv-purple/20"
        >
          <h2 className="font-display text-lg font-semibold text-tv-purple group-hover:underline">MISP Explorer</h2>
          <p className="mt-2 text-sm text-tv-muted">
            Full feeds table, sync servers, taxonomies, statistics, and live sync indicator (30s refresh).
          </p>
        </Link>
      </div>
    </div>
  );
}

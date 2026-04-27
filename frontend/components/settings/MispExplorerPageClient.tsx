"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { MispExplorerPanel } from "@/components/misp/MispExplorerPanel";
import type { IntegrationsGetResponse } from "@/lib/types/integrations";

export function MispExplorerPageClient({ apiEnabled }: { apiEnabled: boolean }) {
  const [integrations, setIntegrations] = useState<IntegrationsGetResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch("/api/threatvision/settings/integrations", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string };
        setLoadError(j.message || `Failed to load (${res.status})`);
        return;
      }
      setIntegrations((await res.json()) as IntegrationsGetResponse);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Network error");
    }
  }, []);

  useEffect(() => {
    if (apiEnabled) void load();
  }, [apiEnabled, load]);

  if (!apiEnabled) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">MISP Explorer</h1>
        <p className="text-tv-muted">Sign in with email/password to use API-backed explorer data.</p>
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  const explorerOk = Boolean(integrations?.misp.explorer_available);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-tv-fg">MISP Explorer</h1>
          <p className="mt-2 max-w-2xl text-sm text-tv-muted">
            Full instance snapshot: feeds, sync partners, taxonomies, and statistics. Configure MISP on the{" "}
            <Link href="/settings/integrations" className="text-tv-cyan hover:underline">
              integrations
            </Link>{" "}
            page (or set platform MISP in the API / <span className="font-mono text-xs">backend/.env</span>).
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg border border-tv-border px-3 py-1.5 text-xs text-tv-muted hover:border-tv-cyan hover:text-tv-cyan"
        >
          Recheck configuration
        </button>
      </div>

      {loadError && (
        <div className="rounded-xl border border-threat-suspicious/40 bg-threat-suspicious/10 p-4 text-sm text-threat-suspicious">
          {loadError}
        </div>
      )}

      {!loadError && integrations && !explorerOk && (
        <div className="rounded-xl border border-tv-border bg-tv-surface/40 p-6 text-sm text-tv-muted">
          <p className="font-medium text-tv-fg">MISP is not wired up yet</p>
          <p className="mt-2">
            Add your MISP <strong className="text-tv-fg">base URL</strong> and <strong className="text-tv-fg">API key</strong>{" "}
            on{" "}
            <Link href="/settings/integrations" className="text-tv-cyan hover:underline">
              Integrations
            </Link>
            , then click <strong className="text-tv-fg">Save integrations</strong>. Alternatively, configure platform
            MISP for all users via Postgres / env (see ThreatVision backend README /{" "}
            <span className="font-mono text-xs">PLATFORM_MISP_*</span> in <span className="font-mono text-xs">.env</span>
            ).
          </p>
          <p className="mt-3 text-xs">
            Until then, this page will not call the explorer API — so you will not see 400 errors in the console for an
            empty setup.
          </p>
        </div>
      )}

      <MispExplorerPanel enabled={explorerOk} compact={false} />
    </div>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";

import type { ProfileResponse } from "@/lib/types/profile";

export function ProfilePageClient() {
  const [data, setData] = useState<ProfileResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const res = await fetch("/api/threatvision/me/profile", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string };
        setErr(j.message || `Failed to load profile (${res.status})`);
        return;
      }
      setData((await res.json()) as ProfileResponse);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onRegenerate() {
    if (!window.confirm("Regenerate API key? The old key stops working immediately.")) return;
    setBusy(true);
    setNewKey(null);
    setErr(null);
    try {
      const res = await fetch("/api/threatvision/me/regenerate-api-key", {
        method: "POST",
        credentials: "include",
      });
      const j = (await res.json().catch(() => ({}))) as { apiKey?: string; detail?: string; message?: string };
      if (!res.ok) {
        setErr(typeof j.detail === "string" ? j.detail : j.message || `Failed (${res.status})`);
        return;
      }
      if (j.apiKey) setNewKey(j.apiKey);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    } finally {
      setBusy(false);
    }
  }

  if (err && !data) {
    return (
      <div className="rounded-lg border border-threat-malicious/40 bg-threat-malicious/10 p-4 text-sm text-threat-malicious">
        {err}
      </div>
    );
  }

  if (!data) {
    return <p className="text-tv-muted">Loading profile…</p>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Profile</h1>
        <p className="mt-2 text-tv-muted">API key for programmatic access; usage from rate-limit counters; recent IOC activity.</p>
      </div>

      {err && (
        <div className="rounded-lg border border-threat-suspicious/40 bg-threat-suspicious/10 px-4 py-3 text-sm text-threat-suspicious">
          {err}
        </div>
      )}

      <section className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">Account</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-tv-muted">Email</dt>
            <dd className="font-mono text-tv-fg">{data.email}</dd>
          </div>
          <div>
            <dt className="text-tv-muted">Role</dt>
            <dd>{data.role}</dd>
          </div>
          <div>
            <dt className="text-tv-muted">Daily limit</dt>
            <dd>{data.unlimited ? "Unlimited" : data.daily_limit.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-tv-muted">Status</dt>
            <dd>{data.banned ? <span className="text-threat-malicious">Banned</span> : "Active"}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <h2 className="font-display text-lg font-semibold text-tv-purple">API key</h2>
        <p className="mt-2 text-sm text-tv-muted">
          Use <code className="rounded bg-tv-void px-1 font-mono text-tv-cyan">Authorization: Bearer &lt;key&gt;</code>{" "}
          on FastAPI routes that accept API keys (e.g. <code className="font-mono">/v1/me</code>). The full secret is
          only shown once after registration or regeneration.
        </p>
        <p className="mt-4 font-mono text-sm text-tv-fg">{data.api_key_masked}</p>
        <button
          type="button"
          disabled={busy || data.banned}
          onClick={() => void onRegenerate()}
          className="mt-4 rounded-lg border border-tv-purple/50 bg-tv-purple/20 px-4 py-2 text-sm font-medium text-tv-fg hover:bg-tv-purple/30 disabled:opacity-50"
        >
          Regenerate API key
        </button>
        {newKey && (
          <div className="mt-4 rounded-lg border border-threat-clean/40 bg-threat-clean/10 p-4">
            <p className="text-sm font-medium text-threat-clean">New key (copy now — won&apos;t be shown again)</p>
            <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all font-mono text-xs text-tv-fg">
              {newKey}
            </pre>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">Usage (UTC days)</h2>
        <dl className="mt-4 flex flex-wrap gap-8 text-sm">
          <div>
            <dt className="text-tv-muted">Today</dt>
            <dd className="font-mono text-xl text-tv-cyan">{data.usage_today.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-tv-muted">Last 7 days</dt>
            <dd className="font-mono text-xl text-tv-cyan">{data.usage_last_7d.toLocaleString()}</dd>
          </div>
        </dl>
        <p className="mt-2 text-xs text-tv-muted">Counts track billable/analysis-style requests (see backend rate limit).</p>
      </section>

      <section className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <h2 className="font-display text-lg font-semibold text-tv-fg">Recent activity</h2>
        <p className="mt-1 text-xs text-tv-muted">Last 25 IOC analyses logged for your account.</p>
        {data.recent_activity.length === 0 ? (
          <p className="mt-4 text-sm text-tv-muted">No activity yet.</p>
        ) : (
          <ul className="mt-4 max-h-80 space-y-2 overflow-y-auto">
            {data.recent_activity.map((a, i) => (
              <li
                key={`${a.created_at}-${i}`}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-tv-border/80 bg-tv-void/40 px-3 py-2 text-sm"
              >
                <code className="font-mono text-tv-cyan">{a.ioc_snippet}</code>
                <span className="text-xs text-tv-muted">{new Date(a.created_at).toLocaleString()}</span>
                <span className="w-full text-xs font-medium uppercase text-tv-muted sm:w-auto">{a.verdict}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

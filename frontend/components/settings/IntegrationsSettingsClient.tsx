"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, useRef } from "react";

import { MispExplorerPanel } from "@/components/misp/MispExplorerPanel";
import type {
  EnricherProbeResult,
  IntegrationsGetResponse,
  IntegrationsPutResponse,
} from "@/lib/types/integrations";

export function IntegrationsSettingsClient() {
  const [data, setData] = useState<IntegrationsGetResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [mispUrl, setMispUrl] = useState("");
  const [mispKey, setMispKey] = useState("");
  const [toggles, setToggles] = useState<Record<string, boolean>>({});
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [mispTestMsg, setMispTestMsg] = useState<string | null>(null);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [probeResults, setProbeResults] = useState<EnricherProbeResult[] | null>(null);

  const debounceRef = useRef<Record<string, NodeJS.Timeout>>({});
  const mispTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mispRef = useRef({ url: "", key: "" });

  useEffect(() => {
    mispRef.current = { url: mispUrl, key: mispKey };
  }, [mispUrl, mispKey]);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch("/api/threatvision/settings/integrations", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string };
        setLoadError(j.message || `Failed to load (${res.status})`);
        return;
      }
      const j = (await res.json()) as IntegrationsGetResponse;
      setData(j);
      setMispUrl(j.misp.base_url ?? "");
      const t: Record<string, boolean> = {};
      const sec: Record<string, string> = {};
      for (const s of j.sources) {
        t[s.id] = s.enabled;
        if (s.configured && s.secret_key) sec[s.secret_key] = "********";
      }
      setToggles(t);
      setSecrets(sec);
      if (j.misp.key_configured) setMispKey("********");
      else setMispKey("");
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Network error");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const mispExplorerEnabled = Boolean(data?.misp.explorer_available);

  async function onTestMisp(isAuto = false, overrideUrl?: string, overrideKey?: string) {
    if (!isAuto) {
      setMispTestMsg(null);
      setBusy(true);
    } else {
      setMispTestMsg("Testing MISP connection...");
    }
    try {
      const u = overrideUrl !== undefined ? overrideUrl : mispUrl;
      const k = overrideKey !== undefined ? overrideKey : mispKey;
      const finalKey = k.trim() === "********" ? undefined : (k.trim() || undefined);

      const res = await fetch("/api/threatvision/settings/misp/test", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_url: u.trim() || undefined,
          api_key: finalKey,
        }),
      });
      const j = (await res.json()) as { ok: boolean; version?: string; detail?: string; resolution?: string };
      if (j.ok) {
        setMispTestMsg(`OK — MISP version ${j.version ?? "?"} (${j.resolution})`);
      } else {
        setMispTestMsg(`Failed (${j.resolution}): ${j.detail ?? "unknown"}`);
      }
    } catch (e) {
      setMispTestMsg(e instanceof Error ? e.message : "Network error");
    } finally {
      if (!isAuto) setBusy(false);
    }
  }

  async function onSave() {
    setSaveMsg(null);
    setBusy(true);
    try {
      const secretPayload: Record<string, string> = {};
      for (const [k, v] of Object.entries(secrets)) {
        if (v.trim() && v !== "********") secretPayload[k] = v.trim();
      }
      const res = await fetch("/api/threatvision/settings/integrations", {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          misp_base_url: mispUrl.trim() || undefined,
          misp_api_key: mispKey.trim() && mispKey !== "********" ? mispKey.trim() : undefined,
          source_toggles: toggles,
          secrets: secretPayload,
        }),
      });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as {
          detail?: string | Array<{ msg?: string }>;
          message?: string;
        };
        let msg = j.message || `Save failed (${res.status})`;
        if (typeof j.detail === "string") msg = j.detail;
        else if (Array.isArray(j.detail) && j.detail.length) {
          msg = j.detail.map((x) => (x && typeof x.msg === "string" ? x.msg : JSON.stringify(x))).join("; ");
        }
        setSaveMsg(msg);
        return;
      }
      const savedBody = (await res.json()) as IntegrationsPutResponse;
      const n = Object.keys(secretPayload).length;
      const slots =
        savedBody.saved_secret_slots?.length && savedBody.saved_secret_slots.length > 0
          ? ` Server now stores: ${savedBody.saved_secret_slots.join(", ")}.`
          : "";
      setSaveMsg((n ? `Saved (${n} key field(s) in this request).` : "Saved.") + slots);
      await load();
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Network error");
    } finally {
      setBusy(false);
    }
  }

  async function onTestEnrichers(sourceId?: string, overrideSecrets?: Record<string, string>) {
    if (!sourceId) {
      setProbeResults(null);
      setBusy(true);
    } else {
      setProbeResults((prev) => {
        const p = prev || [];
        const loadingStatus = { id: sourceId, display_name: sourceId, status: "Testing...", detail: "Auto-test in progress" };
        return [loadingStatus, ...p.filter(x => x.id !== sourceId)];
      });
    }

    try {
      const secretsToUse = overrideSecrets || secrets;
      const override: Record<string, string> = {};
      for (const [k, v] of Object.entries(secretsToUse)) {
        if (v.trim() && v !== "********") override[k] = v.trim();
      }
      const res = await fetch("/api/threatvision/settings/integrations/test-enrichers", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          secrets_override: Object.keys(override).length ? override : undefined,
          source_id: sourceId,
        }),
      });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { detail?: string };
        const errResult = {
            id: sourceId || "_error",
            display_name: sourceId || "Request",
            status: "failed",
            detail: typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`,
        };
        if (sourceId) {
           setProbeResults((prev) => [errResult, ...(prev || []).filter(x => x.id !== sourceId)]);
        } else {
           setProbeResults([errResult]);
        }
        return;
      }
      const j = (await res.json()) as { results: EnricherProbeResult[] };
      if (sourceId) {
         setProbeResults((prev) => {
             const newResults = j.results.filter(x => x.id === sourceId);
             if (!newResults.length) return prev;
             return [...newResults, ...(prev || []).filter(x => x.id !== sourceId)];
         });
      } else {
         setProbeResults(j.results);
      }
    } catch (e) {
      const errResult = {
          id: sourceId || "_error",
          display_name: sourceId || "Request",
          status: "failed",
          detail: e instanceof Error ? e.message : "Network error",
      };
      if (sourceId) {
         setProbeResults((prev) => [errResult, ...(prev || []).filter(x => x.id !== sourceId)]);
      } else {
         setProbeResults([errResult]);
      }
    } finally {
      if (!sourceId) setBusy(false);
    }
  }

  function setToggle(id: string, v: boolean) {
    setToggles((prev) => ({ ...prev, [id]: v }));
  }

  function setSecretAndAutoTest(key: string, v: string, sourceId: string) {
    setSecrets((prev) => {
      const newSecrets = { ...prev, [key]: v };
      if (v.trim() && v !== "********") {
         if (debounceRef.current[sourceId]) clearTimeout(debounceRef.current[sourceId]);
         debounceRef.current[sourceId] = setTimeout(() => {
             void onTestEnrichers(sourceId, newSecrets);
         }, 800);
      }
      return newSecrets;
    });
  }

  function handleMispKeyChange(v: string) {
    setMispKey(v);
    if (v.trim() && v !== "********") {
       if (mispTimeoutRef.current) clearTimeout(mispTimeoutRef.current);
       mispTimeoutRef.current = setTimeout(() => {
           void onTestMisp(true, mispRef.current.url, v);
       }, 800);
    }
  }

  function handleMispUrlChange(v: string) {
    setMispUrl(v);
    if (v.trim()) {
       if (mispTimeoutRef.current) clearTimeout(mispTimeoutRef.current);
       mispTimeoutRef.current = setTimeout(() => {
           void onTestMisp(true, v, mispRef.current.key);
       }, 800);
    }
  }

  if (loadError) {
    return (
      <div className="rounded-lg border border-threat-malicious/40 bg-threat-malicious/10 p-4 text-sm text-threat-malicious">
        {loadError}
      </div>
    );
  }

  if (!data) {
    return <p className="text-tv-muted">Loading integrations…</p>;
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Integrations</h1>
        <p className="mt-2 max-w-2xl text-tv-muted">
          Connect MISP and optional enricher API keys. Secrets are encrypted server-side. Click{" "}
          <strong>Save integrations</strong> after pasting keys — Analyze only reads keys from the server, not unsaved
          fields. Use <strong>Test MISP</strong> to verify MISP before saving; the explorer below appears when MISP is
          resolvable.
        </p>
      </div>

      <section className="rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05] backdrop-blur-sm">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">MISP</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="block text-sm text-tv-muted">Base URL</label>
            <input
              value={mispUrl}
              onChange={(e) => handleMispUrlChange(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm text-tv-fg outline-none focus:border-tv-cyan/60 focus:ring-2 focus:ring-tv-cyan/30"
              placeholder="https://misp.example.org"
              autoComplete="off"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm text-tv-muted">API key</label>
            <input
              type="password"
              value={mispKey}
              onChange={(e) => handleMispKeyChange(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm text-tv-fg outline-none focus:border-tv-cyan/60 focus:ring-2 focus:ring-tv-cyan/30"
              placeholder={data.misp.key_configured ? "•••••••• (leave blank to keep)" : "Required to save"}
              autoComplete="off"
            />
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={busy}
            onClick={() => void onTestMisp()}
            className="rounded-lg border border-tv-purple/50 bg-tv-purple/20 px-4 py-2 text-sm font-medium text-tv-fg hover:bg-tv-purple/30 disabled:opacity-50"
          >
            Test MISP
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void onSave()}
            className="rounded-lg bg-tv-cyan px-4 py-2 text-sm font-medium text-tv-void hover:opacity-95 disabled:opacity-50"
          >
            Save integrations
          </button>
          <Link
            href="/settings/misp"
            className="inline-flex items-center rounded-lg border border-tv-border px-4 py-2 text-sm text-tv-muted hover:border-tv-cyan hover:text-tv-cyan"
          >
            Full MISP explorer →
          </Link>
        </div>
        {mispTestMsg && <p className="mt-3 text-sm text-tv-muted">{mispTestMsg}</p>}
        {saveMsg && (
          <p
            className={`mt-3 text-sm ${saveMsg === "Saved." ? "text-threat-clean" : "text-threat-suspicious"}`}
          >
            {saveMsg}
          </p>
        )}
      </section>

      {mispExplorerEnabled && (
        <section className="rounded-2xl border border-white/[0.08] bg-tv-surface/30 p-6 ring-1 ring-white/[0.04]">
          <MispExplorerPanel enabled compact />
        </section>
      )}

      <section className="rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-lg font-semibold text-tv-purple">Enricher sources</h2>
          <button
            type="button"
            disabled={busy}
            onClick={() => void onTestEnrichers()}
            className="rounded-lg border border-tv-border px-3 py-1.5 text-sm text-tv-muted hover:border-tv-cyan hover:text-tv-cyan disabled:opacity-50"
          >
            Test all (HTTP probes)
          </button>
        </div>
        <p className="mt-1 text-xs text-tv-muted">
          Toggle sources off to skip them during analysis. Keys are merged when you save; test-all uses saved keys
          plus anything you typed below but have not saved yet.
        </p>
        <ul className="mt-6 space-y-4">
          {data.sources.map((s) => (
            <li
              key={s.id}
              className="rounded-xl border border-tv-border/80 bg-tv-void/40 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <span className="font-medium text-tv-fg">{s.display_name}</span>
                  <span className="ml-2 text-xs text-tv-muted">({s.id})</span>
                  {s.configured && s.secret_key && (
                    <span className="ml-2 rounded-full bg-threat-clean/15 px-2 py-0.5 text-[10px] text-threat-clean">
                      Key on file
                    </span>
                  )}
                </div>
                <label className="flex cursor-pointer items-center gap-2 text-sm text-tv-muted">
                  <input
                    type="checkbox"
                    checked={toggles[s.id] ?? true}
                    onChange={(e) => setToggle(s.id, e.target.checked)}
                    className="rounded border-tv-border"
                  />
                  Enabled
                </label>
                {s.secret_key && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void onTestEnrichers(s.id)}
                    className="ml-4 rounded-lg border border-tv-cyan/30 bg-tv-cyan/10 px-3 py-1 text-xs text-tv-cyan hover:bg-tv-cyan/20 disabled:opacity-50"
                  >
                    Test
                  </button>
                )}
              </div>
              {s.secret_key && (
                <div className="mt-3">
                  <label className="text-xs text-tv-muted">
                    {s.requires_api_key ? "API key" : "API key (optional)"}
                  </label>
                  <input
                    type="password"
                    value={secrets[s.secret_key] ?? ""}
                    onChange={(e) => setSecretAndAutoTest(s.secret_key!, e.target.value, s.id)}
                    className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm text-tv-fg outline-none focus:border-tv-cyan/60"
                    placeholder={s.configured ? "•••••••• (leave blank to keep)" : "Paste key to store"}
                    autoComplete="off"
                  />
                  {s.id === "ibm_xforce" && (
                    <p className="mt-1 text-xs text-tv-muted">Format: <code className="font-mono">api_key:api_password</code></p>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>

        {probeResults && (
          <div className="mt-6 rounded-lg border border-tv-border bg-tv-void/50 p-4">
            <p className="text-sm font-medium text-tv-fg">Probe results</p>
            <ul className="mt-2 max-h-64 space-y-1 overflow-y-auto text-xs">
              {probeResults.map((r) => (
                <li key={r.id} className="flex flex-wrap gap-2">
                  <span className="font-mono text-tv-muted">{r.id}</span>
                  <span
                    className={
                      r.status === "ok"
                        ? "text-threat-clean"
                        : r.status === "Testing..."
                          ? "text-tv-cyan animate-pulse"
                          : r.status === "failed"
                            ? "text-threat-malicious"
                            : "text-tv-muted"
                    }
                  >
                    {r.status}
                  </span>
                  {r.detail && <span className="text-tv-muted">— {r.detail}</span>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}

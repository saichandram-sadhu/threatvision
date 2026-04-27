"use client";

import { useCallback, useEffect, useState } from "react";

function formatApiDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return JSON.stringify(detail);
  if (detail && typeof detail === "object" && "msg" in detail) {
    return String((detail as { msg: unknown }).msg);
  }
  return "Request failed";
}

import type { AdminUserRow, PlatformMispState } from "@/lib/types/admin";

export function AdminDashboardClient() {
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [platform, setPlatform] = useState<PlatformMispState | null>(null);
  const [platUrl, setPlatUrl] = useState("");
  const [platKey, setPlatKey] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [newKeys, setNewKeys] = useState<Record<string, string>>({});

  const reload = useCallback(async () => {
    setErr(null);
    try {
      const [ur, pr] = await Promise.all([
        fetch("/api/threatvision/admin/users", { credentials: "include" }),
        fetch("/api/threatvision/admin/platform/misp", { credentials: "include" }),
      ]);
      if (!ur.ok) {
        setErr(`Users: ${ur.status}`);
        return;
      }
      if (!pr.ok) {
        setErr(`Platform MISP: ${pr.status}`);
        return;
      }
      setUsers((await ur.json()) as AdminUserRow[]);
      const p = (await pr.json()) as PlatformMispState;
      setPlatform(p);
      setPlatUrl(p.mispFallbackUrl ?? "");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function patchUser(userId: string, body: Record<string, unknown>) {
    setBusy(true);
    setMsg(null);
    setErr(null);
    try {
      const res = await fetch(`/api/threatvision/admin/users/${userId}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const j = (await res.json().catch(() => ({}))) as { detail?: unknown };
      if (!res.ok) {
        setErr(j.detail != null ? formatApiDetail(j.detail) : `PATCH ${res.status}`);
        return;
      }
      setMsg("User updated.");
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    } finally {
      setBusy(false);
    }
  }

  async function regenKey(userId: string) {
    if (!window.confirm("Regenerate this user's API key?")) return;
    setBusy(true);
    setErr(null);
    try {
      const res = await fetch(`/api/threatvision/admin/users/${userId}/regenerate-api-key`, {
        method: "POST",
        credentials: "include",
      });
      const j = (await res.json().catch(() => ({}))) as { apiKey?: string; detail?: string };
      if (!res.ok) {
        setErr(j.detail || `Regenerate ${res.status}`);
        return;
      }
      if (j.apiKey) setNewKeys((k) => ({ ...k, [userId]: j.apiKey! }));
      setMsg("Key regenerated — copy below.");
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    } finally {
      setBusy(false);
    }
  }

  async function savePlatform() {
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const body: Record<string, string> = {};
      if (platUrl.trim()) body.misp_fallback_url = platUrl.trim();
      if (platKey.trim()) body.misp_fallback_api_key = platKey.trim();
      if (Object.keys(body).length === 0) {
        setErr("Enter URL and/or API key to update.");
        setBusy(false);
        return;
      }
      const res = await fetch("/api/threatvision/admin/platform/misp", {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const j = (await res.json().catch(() => ({}))) as { detail?: string };
      if (!res.ok) {
        setErr(j.detail || `Save ${res.status}`);
        return;
      }
      setPlatKey("");
      setMsg("Platform MISP fallback saved.");
      await reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Network error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Admin</h1>
        <p className="mt-2 text-sm text-tv-muted">Superadmin: users, limits, API keys, platform MISP fallback.</p>
      </div>

      {msg && <p className="rounded-lg border border-threat-clean/40 bg-threat-clean/10 px-4 py-2 text-sm text-threat-clean">{msg}</p>}
      {err && <p className="rounded-lg border border-threat-malicious/40 bg-threat-malicious/10 px-4 py-2 text-sm text-threat-malicious">{err}</p>}

      <section className="rounded-xl border border-white/[0.08] bg-tv-surface/40 p-6 ring-1 ring-white/[0.05]">
        <h2 className="font-display text-lg font-semibold text-tv-cyan">Platform MISP fallback</h2>
        <p className="mt-1 text-xs text-tv-muted">Used when a user has no MISP configured (spec hybrid resolution).</p>
        {platform && (
          <p className="mt-2 text-xs text-tv-muted">
            Key on file: {platform.hasMispFallbackApiKey ? "yes" : "no"}
          </p>
        )}
        <div className="mt-4 grid gap-3 sm:max-w-xl">
          <div>
            <label className="text-sm text-tv-muted">Fallback URL</label>
            <input
              value={platUrl}
              onChange={(e) => setPlatUrl(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm"
              placeholder="https://misp.example.org"
            />
          </div>
          <div>
            <label className="text-sm text-tv-muted">API key</label>
            <input
              type="password"
              value={platKey}
              onChange={(e) => setPlatKey(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm"
              placeholder={platform?.hasMispFallbackApiKey ? "•••••• (leave blank to keep)" : "Required to enable"}
            />
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void savePlatform()}
            className="rounded-lg bg-tv-cyan px-4 py-2 text-sm font-medium text-tv-void disabled:opacity-50"
          >
            Save fallback
          </button>
        </div>
      </section>

      <section className="overflow-x-auto rounded-xl border border-white/[0.08] ring-1 ring-white/[0.04]">
        <table className="w-full min-w-[960px] text-left text-sm">
          <thead className="border-b border-tv-border bg-tv-void/50 text-xs uppercase text-tv-muted">
            <tr>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Daily limit</th>
              <th className="px-3 py-2">Flags</th>
              <th className="px-3 py-2">Key prefix</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-tv-border/60">
            {users.map((u) => (
              <UserRow
                key={u.userId}
                u={u}
                busy={busy}
                newKey={newKeys[u.userId]}
                onPatch={(body) => void patchUser(u.userId, body)}
                onRegen={() => void regenKey(u.userId)}
              />
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function UserRow({
  u,
  busy,
  newKey,
  onPatch,
  onRegen,
}: {
  u: AdminUserRow;
  busy: boolean;
  newKey?: string;
  onPatch: (body: Record<string, unknown>) => void;
  onRegen: () => void;
}) {
  const [limit, setLimit] = useState(String(u.dailyLimit));

  useEffect(() => {
    setLimit(String(u.dailyLimit));
  }, [u.dailyLimit]);

  return (
    <>
      <tr className="bg-tv-surface/20">
        <td className="px-3 py-2 font-mono text-xs text-tv-cyan">{u.email}</td>
        <td className="px-3 py-2">{u.role}</td>
        <td className="px-3 py-2">
          <input
            type="number"
            min={1}
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="w-24 rounded border border-tv-border bg-tv-void px-2 py-1 font-mono text-xs"
            disabled={u.unlimited}
          />
          <button
            type="button"
            disabled={busy || u.unlimited}
            onClick={() => onPatch({ dailyLimit: Math.max(1, parseInt(limit, 10) || 1) })}
            className="ml-2 text-xs text-tv-cyan hover:underline disabled:opacity-40"
          >
            Set limit
          </button>
        </td>
        <td className="px-3 py-2">
          <label className="mr-3 inline-flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={u.unlimited}
              onChange={(e) => onPatch({ unlimited: e.target.checked })}
              disabled={busy}
            />
            Unlimited
          </label>
          <label className="inline-flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={u.banned}
              onChange={(e) => onPatch({ banned: e.target.checked })}
              disabled={busy}
            />
            Banned
          </label>
        </td>
        <td className="px-3 py-2 font-mono text-xs text-tv-muted">{u.apiKeyPrefix ?? "—"}</td>
        <td className="space-y-1 px-3 py-2">
          <button
            type="button"
            disabled={busy}
            onClick={onRegen}
            className="block text-xs text-tv-purple hover:underline disabled:opacity-40"
          >
            Regenerate key
          </button>
          <div className="text-[10px] text-tv-muted">{new Date(u.createdAt).toLocaleDateString()}</div>
        </td>
      </tr>
      {newKey && (
        <tr className="bg-threat-clean/5">
          <td colSpan={6} className="px-3 py-2 font-mono text-xs text-threat-clean">
            New key for {u.email}: {newKey}
          </td>
        </tr>
      )}
    </>
  );
}

"use client";

import { useCallback, useEffect, useState } from "react";

import type { MispExplorerResponse } from "@/lib/types/misp-explorer";

type State = {
  data: MispExplorerResponse | null;
  error: string | null;
  loading: boolean;
};

export function useMispExplorer(enabled: boolean, intervalMs = 30_000) {
  const [state, setState] = useState<State>({ data: null, error: null, loading: enabled });

  const load = useCallback(async () => {
    if (!enabled) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    setState((s) => ({ ...s, loading: s.data === null, error: null }));
    try {
      const res = await fetch("/api/threatvision/misp/explorer", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as {
          detail?: string | Array<{ msg?: string }>;
          message?: string;
          error?: string;
        };
        const detailStr =
          typeof j.detail === "string"
            ? j.detail
            : Array.isArray(j.detail)
              ? j.detail.map((x) => (x && typeof x.msg === "string" ? x.msg : JSON.stringify(x))).join("; ")
              : undefined;
        const msg =
          detailStr ||
          j.message ||
          (typeof j.error === "string" ? j.error : undefined) ||
          `Explorer failed (${res.status})`;
        setState({ data: null, error: msg, loading: false });
        return;
      }
      const data = (await res.json()) as MispExplorerResponse;
      setState({ data, error: null, loading: false });
    } catch (e) {
      setState({
        data: null,
        error: e instanceof Error ? e.message : "Network error",
        loading: false,
      });
    }
  }, [enabled]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!enabled) return;
    const t = window.setInterval(() => void load(), intervalMs);
    return () => window.clearInterval(t);
  }, [enabled, intervalMs, load]);

  return { ...state, refetch: load };
}

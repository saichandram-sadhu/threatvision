"use client";

import { useCallback, useEffect, useState } from "react";

import type { DashboardStats } from "@/lib/types/dashboard";

type State = {
  data: DashboardStats | null;
  error: string | null;
  loading: boolean;
};

export function useDashboardStats(enabled: boolean) {
  const [state, setState] = useState<State>({
    data: null,
    error: null,
    loading: enabled,
  });

  const load = useCallback(async () => {
    if (!enabled) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    setState((s) => ({ ...s, loading: s.data === null, error: null }));
    try {
      const res = await fetch("/api/threatvision/stats/dashboard", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string; error?: string };
        const msg = j.message || j.error || `Request failed (${res.status})`;
        setState({ data: null, error: msg, loading: false });
        return;
      }
      const data = (await res.json()) as DashboardStats;
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
    const t = window.setInterval(() => void load(), 60_000);
    return () => window.clearInterval(t);
  }, [enabled, load]);

  return { ...state, refetch: load };
}

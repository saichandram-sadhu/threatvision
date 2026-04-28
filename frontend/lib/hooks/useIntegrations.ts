"use client";

import { useCallback, useEffect, useState } from "react";
import type { IntegrationsGetResponse } from "@/lib/types/integrations";

type State = {
  data: IntegrationsGetResponse | null;
  error: string | null;
  loading: boolean;
};

export function useIntegrations(enabled: boolean) {
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
      const res = await fetch("/api/threatvision/settings/integrations", { credentials: "include" });
      if (!res.ok) {
        const j = (await res.json().catch(() => ({}))) as { message?: string; error?: string };
        const msg = j.message || j.error || `Request failed (${res.status})`;
        setState({ data: null, error: msg, loading: false });
        return;
      }
      const data = (await res.json()) as IntegrationsGetResponse;
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

  return { ...state, refetch: load };
}

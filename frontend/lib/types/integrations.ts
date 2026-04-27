export type IntegrationSourceState = {
  id: string;
  display_name: string;
  requires_api_key: boolean;
  enabled: boolean;
  configured: boolean;
  secret_key: string | null;
};

export type IntegrationsGetResponse = {
  misp: {
    base_url: string | null;
    key_configured: boolean;
    /** Backend can resolve MISP (user, platform, or env) — safe to load explorer */
    explorer_available: boolean;
  };
  sources: IntegrationSourceState[];
};

export type IntegrationsPutResponse = {
  saved: boolean;
  saved_secret_slots?: string[];
};

export type EnricherProbeResult = {
  id: string;
  display_name: string;
  status: string;
  detail: string | null;
};

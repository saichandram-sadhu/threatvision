export type MispFeedRow = {
  id: string | null;
  name: string | null;
  url: string | null;
  source_format: string | null;
  enabled: boolean | null;
  last_fetch: string | null;
  event_count: number | null;
  live_sync: boolean | null;
  cache_age_seconds: number | null;
};

export type MispServerRow = {
  id: string | null;
  name: string | null;
  url: string | null;
  push: boolean | null;
  pull: boolean | null;
  last_sync: string | null;
  sync_status: string | null;
  event_count: number | null;
};

export type MispTaxonomyRow = {
  namespace: string | null;
  enabled: boolean | null;
  description: string | null;
};

export type MispStatsPanel = {
  total_events: number | null;
  total_attributes: number | null;
  total_objects: number | null;
  feeds_configured: number | null;
  feeds_enabled: number | null;
  connected_servers: number | null;
  misp_version: string | null;
  last_event_added: string | null;
};

export type MispExplorerResponse = {
  connected: boolean;
  base_url: string;
  resolution: string;
  misp_version: string | null;
  feeds: MispFeedRow[];
  servers: MispServerRow[];
  taxonomies: MispTaxonomyRow[];
  stats: MispStatsPanel;
  sync_indicator: string;
  source_errors: Record<string, string>;
  fetched_at: string;
};

export type VerdictBucket = {
  verdict: string;
  count: number;
};

export type TopIpRow = {
  ip: string;
  count: number;
};

export type DashboardStats = {
  analyses_1d: number;
  analyses_7d: number;
  analyses_30d: number;
  analyses_all: number;
  verdict_distribution_30d: VerdictBucket[];
  top_ips_30d: TopIpRow[];
};

export type FlaggedByChip = {
  id: string;
  display_name: string;
};

export type ActivityRecentItem = {
  id: string;
  ioc_snippet: string;
  verdict: string;
  created_at: string;
  flagged_by: FlaggedByChip[];
};

export type ActivityRecentResponse = {
  items: ActivityRecentItem[];
};

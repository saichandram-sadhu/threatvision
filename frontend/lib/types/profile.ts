export type ProfileActivityItem = {
  ioc_snippet: string;
  verdict: string;
  created_at: string;
};

export type ProfileResponse = {
  user_id: string;
  email: string;
  role: string;
  api_key_masked: string;
  has_api_key: boolean;
  daily_limit: number;
  unlimited: boolean;
  banned: boolean;
  usage_today: number;
  usage_last_7d: number;
  recent_activity: ProfileActivityItem[];
};

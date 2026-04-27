export type AdminUserRow = {
  userId: string;
  email: string;
  role: string;
  dailyLimit: number;
  unlimited: boolean;
  banned: boolean;
  apiKeyPrefix: string | null;
  createdAt: string;
};

export type PlatformMispState = {
  mispFallbackUrl: string | null;
  hasMispFallbackApiKey: boolean;
};

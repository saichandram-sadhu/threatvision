export type SourceStatus = "ok" | "not_configured" | "unavailable";
export type SourceVerdict = "clean" | "suspicious" | "malicious" | "unknown";
export type AggregateVerdict = "CLEAN" | "SUSPICIOUS" | "MALICIOUS";

export type MispEventInfo = {
  eventId: string;
  eventName: string;
  tags: string[];
  tlp: string;
  feedName: string | null;
};

export type SourceResult = {
  id: string;
  displayName: string;
  status: SourceStatus;
  verdict: SourceVerdict | null;
  detailLines: string[];
  metadata: Record<string, unknown>;
  errorCode: string | null;
};

export type IocPayload = {
  raw: string;
  normalized: string;
  type: string;
};

export type AggregateResult = {
  verdict: AggregateVerdict;
  confidence: number;
  rationale: string | null;
};

export type AnalyzeResponse = {
  ioc: IocPayload;
  aggregate: AggregateResult;
  sources: SourceResult[];
};

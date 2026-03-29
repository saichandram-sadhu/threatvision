import { SOURCE_CATALOG_IDS } from "@/lib/ioc/catalogOrder";
import type { AnalyzeResponse } from "@/lib/types/analyze";

function csvCell(s: string): string {
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function buildBulkCsv(rows: AnalyzeResponse[]): string {
  const header = [
    "ioc",
    "type",
    "aggregate_verdict",
    "confidence",
    ...SOURCE_CATALOG_IDS.map((id) => `src_${id}`),
  ];
  const lines = [header.join(",")];
  for (const r of rows) {
    const byId = new Map(r.sources.map((s) => [s.id, s]));
    const cells = [
      csvCell(r.ioc.normalized),
      csvCell(r.ioc.type),
      csvCell(r.aggregate.verdict),
      String(r.aggregate.confidence),
      ...SOURCE_CATALOG_IDS.map((id) => {
        const s = byId.get(id);
        if (!s) return "";
        if (s.status !== "ok") return csvCell(s.status);
        return csvCell(s.verdict ?? "");
      }),
    ];
    lines.push(cells.join(","));
  }
  return lines.join("\n");
}

export function buildBulkJson(rows: AnalyzeResponse[]): string {
  return JSON.stringify(rows, null, 2);
}

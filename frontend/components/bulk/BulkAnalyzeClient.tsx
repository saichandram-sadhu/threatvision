"use client";

import { useCallback, useRef, useState } from "react";

import { VendorDotsRow } from "@/components/ioc/VendorDotsRow";
import { buildBulkCsv, buildBulkJson } from "@/lib/ioc/exportBulk";
import type { AnalyzeResponse } from "@/lib/types/analyze";

function parseIocsBlock(text: string): string[] {
  const parts = text
    .split(/[\r\n,;\t]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return Array.from(new Set(parts));
}

type BulkRow =
  | { status: "pending"; position: number; iocRaw: string }
  | { status: "done"; position: number; iocRaw: string; result: AnalyzeResponse }
  | { status: "error"; position: number; iocRaw: string; error: string };

function downloadText(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function BulkAnalyzeClient() {
  const [text, setText] = useState("");
  const [rows, setRows] = useState<BulkRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const stopStream = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  const finalizeExports = useCallback(() => {
    setBusy(false);
  }, []);

  const startJob = useCallback(
    async (iocs: string[]) => {
      setErr(null);
      setJobStatus(null);
      stopStream();
      setBusy(true);
      setRows(iocs.map((iocRaw, position) => ({ status: "pending", position, iocRaw })));

      try {
        const res = await fetch("/api/threatvision/ioc/bulk", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ iocs }),
        });
        const data = (await res.json().catch(() => ({}))) as {
          jobId?: string;
          detail?: unknown;
          message?: string;
        };
        if (!res.ok) {
          const d = data.detail;
          let msg = data.message || `Bulk start failed (${res.status})`;
          if (typeof d === "string") msg = d;
          else if (Array.isArray(d) && d[0] && typeof d[0] === "object" && d[0] !== null && "msg" in d[0]) {
            msg = String((d[0] as { msg: unknown }).msg);
          }
          setErr(msg);
          setBusy(false);
          setRows([]);
          return;
        }
        const jobId = data.jobId;
        if (!jobId) {
          setErr("No job id returned");
          setBusy(false);
          setRows([]);
          return;
        }

        const es = new EventSource(`/api/threatvision/ioc/bulk/${jobId}/stream`, {
          withCredentials: true,
        });
        esRef.current = es;

        es.addEventListener("item", (ev) => {
          try {
            const payload = JSON.parse((ev as MessageEvent).data) as {
              type?: string;
              position?: number;
              iocRaw?: string;
              result?: AnalyzeResponse;
              error?: string;
            };
            const pos = Number(payload.position);
            if (Number.isNaN(pos)) return;
            setRows((prev) => {
              const next = [...prev];
              if (payload.result) {
                next[pos] = {
                  status: "done",
                  position: pos,
                  iocRaw: payload.iocRaw ?? next[pos]?.iocRaw ?? "",
                  result: payload.result,
                };
              } else if (payload.error) {
                next[pos] = {
                  status: "error",
                  position: pos,
                  iocRaw: payload.iocRaw ?? next[pos]?.iocRaw ?? "",
                  error: payload.error,
                };
              }
              return next;
            });
          } catch {
            /* ignore malformed */
          }
        });

        es.addEventListener("done", (ev) => {
          try {
            const payload = JSON.parse((ev as MessageEvent).data) as { jobStatus?: string };
            setJobStatus(payload.jobStatus ?? "done");
          } catch {
            setJobStatus("done");
          }
          stopStream();
          finalizeExports();
        });

        es.onerror = () => {
          stopStream();
          setJobStatus((s) => s ?? "stream_error");
          finalizeExports();
        };
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Network error");
        setBusy(false);
        setRows([]);
      }
    },
    [finalizeExports, stopStream],
  );

  const onRun = () => {
    const iocs = parseIocsBlock(text);
    if (iocs.length === 0) {
      setErr("Enter at least one IOC.");
      return;
    }
    if (iocs.length > 500) {
      setErr("Maximum 500 IOCs per job.");
      return;
    }
    void startJob(iocs);
  };

  const onFile = async (f: File | null) => {
    if (!f) return;
    const t = await f.text();
    setText((prev) => (prev ? `${prev}\n${t}` : t));
  };

  const analysesDone = rows
    .filter((r): r is Extract<BulkRow, { status: "done" }> => r.status === "done")
    .sort((a, b) => a.position - b.position)
    .map((r) => r.result);

  async function onPdf() {
    if (analysesDone.length === 0) return;
    const slice = analysesDone.slice(0, 50);
    const res = await fetch("/api/threatvision/reports/pdf", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ analyses: slice }),
    });
    if (!res.ok) {
      const msg = await res.text();
      setErr(`PDF: ${msg.slice(0, 200)}`);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "threatvision-bulk-report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Bulk analyze</h1>
        <p className="mt-2 max-w-2xl text-sm text-tv-muted">
          Paste IOCs (newline, comma, or semicolon separated) or append a file. Progress streams over SSE; export CSV,
          JSON, or PDF (first 50 results).
        </p>
      </div>

      <div className="space-y-3">
        <label className="block text-sm text-tv-muted">IOCs</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={8}
          className="w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 font-mono text-sm text-tv-fg outline-none focus:border-tv-cyan/60"
          placeholder="8.8.8.8&#10;evil.example&#10;…"
        />
        <div className="flex flex-wrap gap-3">
          <label className="cursor-pointer rounded-lg border border-tv-border px-3 py-2 text-sm text-tv-muted hover:border-tv-cyan">
            Append file
            <input type="file" accept=".txt,.csv,text/plain" className="hidden" onChange={(e) => void onFile(e.target.files?.[0] ?? null)} />
          </label>
          <button
            type="button"
            disabled={busy}
            onClick={() => onRun()}
            className="rounded-lg bg-tv-cyan px-5 py-2 text-sm font-medium text-tv-void hover:opacity-95 disabled:opacity-50"
          >
            {busy ? "Running…" : "Run bulk job"}
          </button>
        </div>
      </div>

      {err && (
        <div className="rounded-lg border border-threat-malicious/40 bg-threat-malicious/10 px-4 py-3 text-sm text-threat-malicious">
          {err}
        </div>
      )}

      {jobStatus && (
        <p className="text-sm text-tv-muted">
          Job status: <span className="font-mono text-tv-cyan">{jobStatus}</span>
        </p>
      )}

      {rows.length > 0 && (
        <>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={analysesDone.length === 0}
              onClick={() => downloadText("threatvision-bulk.json", buildBulkJson(analysesDone), "application/json")}
              className="rounded-lg border border-tv-border px-3 py-1.5 text-sm text-tv-muted hover:border-tv-cyan disabled:opacity-40"
            >
              Export JSON
            </button>
            <button
              type="button"
              disabled={analysesDone.length === 0}
              onClick={() => downloadText("threatvision-bulk.csv", buildBulkCsv(analysesDone), "text/csv")}
              className="rounded-lg border border-tv-border px-3 py-1.5 text-sm text-tv-muted hover:border-tv-cyan disabled:opacity-40"
            >
              Export CSV
            </button>
            <button
              type="button"
              disabled={analysesDone.length === 0}
              onClick={() => void onPdf()}
              className="rounded-lg border border-tv-purple/40 bg-tv-purple/15 px-3 py-1.5 text-sm text-tv-accent hover:bg-tv-purple/25 disabled:opacity-40"
            >
              Export PDF (max 50)
            </button>
            {analysesDone.length > 50 && (
              <span className="self-center text-xs text-tv-muted">PDF uses first 50 completed rows.</span>
            )}
          </div>

          <div className="overflow-x-auto rounded-xl border border-white/[0.08] ring-1 ring-white/[0.04]">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-tv-border bg-tv-void/50 text-xs uppercase tracking-wide text-tv-muted">
                <tr>
                  <th className="px-3 py-2 font-medium">#</th>
                  <th className="px-3 py-2 font-medium">IOC</th>
                  <th className="px-3 py-2 font-medium">Aggregate</th>
                  <th className="px-3 py-2 font-medium">Vendors</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-tv-border/60">
                {rows.map((r) => (
                  <tr key={r.position} className="bg-tv-surface/20">
                    <td className="px-3 py-2 font-mono text-xs text-tv-muted">{r.position + 1}</td>
                    <td className="max-w-[200px] truncate px-3 py-2 font-mono text-xs text-tv-cyan" title={r.iocRaw}>
                      {r.iocRaw}
                    </td>
                    <td className="px-3 py-2">
                      {r.status === "pending" && <span className="text-tv-muted">…</span>}
                      {r.status === "error" && (
                        <span className="text-threat-malicious" title={r.error}>
                          Error
                        </span>
                      )}
                      {r.status === "done" && (
                        <span
                          className={
                            r.result.aggregate.verdict === "MALICIOUS"
                              ? "text-threat-malicious"
                              : r.result.aggregate.verdict === "SUSPICIOUS"
                                ? "text-threat-suspicious"
                                : "text-threat-clean"
                          }
                        >
                          {r.result.aggregate.verdict}{" "}
                          <span className="text-tv-muted">({r.result.aggregate.confidence})</span>
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {r.status === "done" ? <VendorDotsRow sources={r.result.sources} /> : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

import { formatRelativeIso } from "@/lib/format/relativeTime";

export function SyncIndicator({
  syncIndicator,
  fetchedAt,
}: {
  syncIndicator: string;
  fetchedAt: string;
}) {
  const ind = syncIndicator.toLowerCase();
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-white/[0.08] bg-tv-void/50 px-4 py-3">
      <div className="flex items-center gap-2">
        <span
          className={
            ind === "error"
              ? "h-2.5 w-2.5 rounded-full bg-threat-malicious shadow-[0_0_10px_rgba(255,45,85,0.6)]"
              : ind === "syncing"
                ? "h-2.5 w-2.5 animate-pulse rounded-full bg-threat-clean shadow-[0_0_10px_rgba(0,255,136,0.5)]"
                : "h-2.5 w-2.5 rounded-full bg-tv-muted"
          }
          aria-hidden
        />
        <span className="text-sm font-medium capitalize text-tv-fg">{syncIndicator}</span>
      </div>
      <span className="text-xs text-tv-muted">Snapshot {formatRelativeIso(fetchedAt)}</span>
    </div>
  );
}

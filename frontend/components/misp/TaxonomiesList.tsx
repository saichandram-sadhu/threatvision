import type { MispTaxonomyRow } from "@/lib/types/misp-explorer";

export function TaxonomiesList({ taxonomies }: { taxonomies: MispTaxonomyRow[] }) {
  if (taxonomies.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-tv-border py-6 text-center text-sm text-tv-muted">
        No taxonomies listed.
      </p>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-tv-surface/35 p-5 ring-1 ring-white/[0.04]">
      <h3 className="font-display text-sm font-semibold text-tv-fg">Taxonomies</h3>
      <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto pr-1 text-sm">
        {taxonomies.map((t, i) => (
          <li
            key={`${t.namespace}-${i}`}
            className="flex items-start justify-between gap-2 rounded-lg border border-tv-border/80 bg-tv-void/40 px-3 py-2"
          >
            <div>
              <span className="font-medium text-tv-cyan">{t.namespace ?? "—"}</span>
              {t.description && <p className="mt-0.5 text-xs text-tv-muted">{t.description}</p>}
            </div>
            <span
              className={
                t.enabled
                  ? "shrink-0 rounded-full bg-threat-clean/15 px-2 py-0.5 text-[10px] font-medium uppercase text-threat-clean"
                  : "shrink-0 rounded-full bg-tv-muted/20 px-2 py-0.5 text-[10px] font-medium uppercase text-tv-muted"
              }
            >
              {t.enabled ? "On" : "Off"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

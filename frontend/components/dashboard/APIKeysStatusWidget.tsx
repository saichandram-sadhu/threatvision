"use client";

import { motion } from "framer-motion";
import { useIntegrations } from "@/lib/hooks/useIntegrations";

type Props = {
  enabled: boolean;
};

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-threat-benign">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const CrossIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-threat-malicious">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-tv-accent">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
  </svg>
);

const KeyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-tv-accent">
    <path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3L15.5 7.5z"></path>
  </svg>
);

export function APIKeysStatusWidget({ enabled }: Props) {
  const { data, loading, error } = useIntegrations(enabled);

  if (!enabled) return null;

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05
      }
    }
  };

  const item = {
    hidden: { opacity: 0, scale: 0.95 },
    show: { opacity: 1, scale: 1 }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldIcon />
          <h2 className="font-display text-lg font-semibold text-tv-fg">API keys status</h2>
        </div>
        <span className="rounded bg-tv-surface/60 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-tv-muted shadow-inner ring-1 ring-white/5">Superadmin only</span>
      </div>

      <div className="overflow-hidden rounded-2xl border border-white/[0.06] bg-gradient-to-br from-tv-surface/40 to-tv-void/40 p-6 shadow-xl backdrop-blur-md">
        {loading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-xl bg-tv-surface/50" />
            ))}
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 rounded-xl border border-threat-malicious/20 bg-threat-malicious/5 p-4 text-sm text-threat-malicious">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
            <p>Failed to load integration status: {error}</p>
          </div>
        ) : (
          <motion.div 
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
          >
            {/* MISP Status */}
            <motion.div 
              variants={item} 
              className="group flex items-center justify-between rounded-xl border border-white/[0.03] bg-white/[0.02] p-3.5 transition-all hover:bg-white/[0.04] hover:shadow-lg"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-tv-accent/10 text-tv-accent transition-transform group-hover:scale-110">
                  <KeyIcon />
                </div>
                <div className="flex flex-col">
                  <span className="text-xs font-semibold text-tv-fg uppercase tracking-wider">MISP</span>
                  <span className="text-[10px] text-tv-muted uppercase font-medium">Core Service</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {data?.misp.key_configured ? (
                  <div className="flex items-center gap-1.5 rounded-full bg-threat-benign/10 px-2 py-1">
                    <CheckIcon />
                    <span className="text-[10px] font-bold text-threat-benign uppercase">Active</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 rounded-full bg-threat-malicious/10 px-2 py-1">
                    <CrossIcon />
                    <span className="text-[10px] font-bold text-threat-malicious uppercase">Missing</span>
                  </div>
                )}
              </div>
            </motion.div>

            {/* External Enrichers */}
            {data?.sources.filter(s => s.requires_api_key).map((s) => (
              <motion.div 
                key={s.id} 
                variants={item}
                className="group flex items-center justify-between rounded-xl border border-white/[0.03] bg-white/[0.02] p-3.5 transition-all hover:bg-white/[0.04] hover:shadow-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-tv-accent/10 text-tv-accent transition-transform group-hover:scale-110">
                    <KeyIcon />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-tv-fg uppercase tracking-wider">{s.display_name}</span>
                    <span className="text-[10px] text-tv-muted uppercase font-medium">Enricher</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {s.configured ? (
                    <div className="flex items-center gap-1.5 rounded-full bg-threat-benign/10 px-2 py-1">
                      <CheckIcon />
                      <span className="text-[10px] font-bold text-threat-benign uppercase">Active</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 rounded-full bg-threat-malicious/10 px-2 py-1">
                      <CrossIcon />
                      <span className="text-[10px] font-bold text-threat-malicious uppercase">Missing</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  );
}

"use client";

import Link from "next/link";

import { MispExplorerPanel } from "@/components/misp/MispExplorerPanel";

export function MispExplorerPageClient({ apiEnabled }: { apiEnabled: boolean }) {
  if (!apiEnabled) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">MISP Explorer</h1>
        <p className="text-tv-muted">Sign in with email/password to use API-backed explorer data.</p>
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold text-tv-fg">MISP Explorer</h1>
          <p className="mt-2 max-w-2xl text-sm text-tv-muted">
            Full instance snapshot: feeds, sync partners, taxonomies, and statistics. Configure MISP on the{" "}
            <Link href="/settings/integrations" className="text-tv-cyan hover:underline">
              integrations
            </Link>{" "}
            page.
          </p>
        </div>
      </div>
      <MispExplorerPanel enabled compact={false} />
    </div>
  );
}

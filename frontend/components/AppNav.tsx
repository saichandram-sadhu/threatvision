"use client";

import Link from "next/link";
import { signOut, useSession } from "next-auth/react";

export function AppNav() {
  const { data: session } = useSession();

  return (
    <header className="border-b border-tv-border bg-tv-void/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <div className="flex items-center gap-6">
          <Link
            href="/dashboard"
            className="font-display text-lg font-semibold tracking-tight text-tv-cyan"
          >
            ThreatVision
          </Link>
          <nav className="hidden gap-4 text-sm text-tv-muted sm:flex">
            <Link href="/dashboard" className="hover:text-tv-cyan">
              Dashboard
            </Link>
            <Link href="/settings" className="hover:text-tv-cyan">
              Settings
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {session?.user?.email && (
            <span className="hidden max-w-[200px] truncate text-tv-muted md:inline">
              {session.user.email}
            </span>
          )}
          <button
            type="button"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="rounded-md border border-tv-border px-3 py-1.5 text-tv-muted hover:border-tv-cyan hover:text-tv-cyan"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}

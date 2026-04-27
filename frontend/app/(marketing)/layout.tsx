import Link from "next/link";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-tv-void text-tv-fg">
      <header className="border-b border-tv-border bg-tv-void/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-4">
          <Link href="/" className="font-display text-lg font-semibold text-tv-cyan">
            ThreatVision
          </Link>
          <nav className="flex gap-4 text-sm text-tv-muted">
            <Link href="/about" className="hover:text-tv-cyan">
              About
            </Link>
            <Link href="/login" className="hover:text-tv-cyan">
              Sign in
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-12">{children}</main>
    </div>
  );
}

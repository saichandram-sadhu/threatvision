import Link from "next/link";
import { Suspense } from "react";

import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <div className="flex w-full max-w-md flex-col items-center">
      <Suspense
        fallback={
          <div className="w-full rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-8 text-center text-tv-muted ring-1 ring-white/[0.06] backdrop-blur-xl">
            Loading…
          </div>
        }
      >
        <LoginForm
          googleEnabled={Boolean(process.env.GOOGLE_CLIENT_ID)}
          githubEnabled={Boolean(process.env.GITHUB_ID)}
        />
      </Suspense>
      <Link
        href="/about"
        className="mt-8 text-sm text-tv-muted transition-colors hover:text-tv-cyan"
      >
        About ThreatVision
      </Link>
    </div>
  );
}

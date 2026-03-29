import { Suspense } from "react";

import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-md rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-8 text-center text-tv-muted ring-1 ring-white/[0.06] backdrop-blur-xl">
          Loading…
        </div>
      }
    >
      <LoginForm
        googleEnabled={Boolean(process.env.GOOGLE_CLIENT_ID)}
        githubEnabled={Boolean(process.env.GITHUB_ID)}
      />
    </Suspense>
  );
}

import { Suspense } from "react";

import { LoginForm } from "@/components/auth/LoginForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="w-full max-w-md rounded-xl border border-tv-border bg-tv-surface p-8 text-center text-tv-muted">
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

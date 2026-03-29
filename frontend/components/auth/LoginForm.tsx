"use client";

import Link from "next/link";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

type Props = {
  googleEnabled: boolean;
  githubEnabled: boolean;
};

export function LoginForm({ googleEnabled, githubEnabled }: Props) {
  const router = useRouter();
  const search = useSearchParams();
  const callbackUrl = search.get("callbackUrl") || "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
      callbackUrl,
    });
    setPending(false);
    if (res?.error) {
      setError("Invalid email or password.");
      return;
    }
    router.push(callbackUrl);
    router.refresh();
  }

  const showOAuth = googleEnabled || githubEnabled;

  return (
    <div className="w-full max-w-md space-y-8 rounded-xl border border-tv-border bg-tv-surface p-8 shadow-lg shadow-tv-purple/5">
      <div>
        <h1 className="font-display text-2xl font-bold text-tv-cyan">ThreatVision</h1>
        <p className="mt-1 text-sm text-tv-muted">Sign in to continue</p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm text-tv-muted">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-tv-border bg-tv-void px-3 py-2 text-tv-fg outline-none focus:border-tv-cyan"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm text-tv-muted">
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-tv-border bg-tv-void px-3 py-2 text-tv-fg outline-none focus:border-tv-cyan"
          />
        </div>
        {error && <p className="text-sm text-threat-malicious">{error}</p>}
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-md bg-tv-cyan px-4 py-2 font-medium text-tv-void hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>

      {showOAuth && (
        <div className="flex flex-col gap-2 border-t border-tv-border pt-6">
          <p className="text-center text-xs text-tv-muted">OAuth (optional)</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            {googleEnabled && (
              <button
                type="button"
                onClick={() => signIn("google", { callbackUrl })}
                className="flex-1 rounded-md border border-tv-border py-2 text-sm text-tv-muted hover:border-tv-purple hover:text-tv-fg"
              >
                Google
              </button>
            )}
            {githubEnabled && (
              <button
                type="button"
                onClick={() => signIn("github", { callbackUrl })}
                className="flex-1 rounded-md border border-tv-border py-2 text-sm text-tv-muted hover:border-tv-purple hover:text-tv-fg"
              >
                GitHub
              </button>
            )}
          </div>
          <p className="text-center text-xs text-tv-muted">
            OAuth sessions cannot call the BFF until account linking exists — use email/password for API
            access.
          </p>
        </div>
      )}

      <p className="text-center text-sm text-tv-muted">
        No account?{" "}
        <Link href="/register" className="text-tv-cyan hover:underline">
          Register
        </Link>
      </p>
    </div>
  );
}

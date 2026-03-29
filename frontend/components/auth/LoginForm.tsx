"use client";

import { motion, useReducedMotion } from "framer-motion";
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
  const reduceMotion = useReducedMotion();

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
    <motion.div
      className="w-full max-w-md space-y-8 rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-8 shadow-2xl shadow-black/40 ring-1 ring-white/[0.06] backdrop-blur-xl"
      initial={reduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    >
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-tv-cyan drop-shadow-[0_0_24px_rgba(34,211,238,0.25)]">
          ThreatVision
        </h1>
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
            className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 text-tv-fg outline-none ring-tv-cyan/30 placeholder:text-tv-muted focus:border-tv-cyan/60 focus:ring-2"
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
            className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 text-tv-fg outline-none ring-tv-cyan/30 placeholder:text-tv-muted focus:border-tv-cyan/60 focus:ring-2"
          />
        </div>
        {error && <p className="text-sm text-threat-malicious">{error}</p>}
        <button
          type="submit"
          disabled={pending}
          className="w-full rounded-lg bg-tv-cyan px-4 py-2.5 font-medium text-tv-void shadow-lg shadow-tv-cyan/20 transition hover:opacity-95 disabled:opacity-50"
        >
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>

      {showOAuth && (
        <div className="flex flex-col gap-2 border-t border-white/[0.08] pt-6">
          <p className="text-center text-xs text-tv-muted">OAuth (optional)</p>
          <div className="flex flex-col gap-2 sm:flex-row">
            {googleEnabled && (
              <button
                type="button"
                onClick={() => signIn("google", { callbackUrl })}
                className="flex-1 rounded-lg border border-white/[0.1] bg-tv-void/40 py-2 text-sm text-tv-muted backdrop-blur-sm transition hover:border-tv-purple/50 hover:text-tv-fg"
              >
                Google
              </button>
            )}
            {githubEnabled && (
              <button
                type="button"
                onClick={() => signIn("github", { callbackUrl })}
                className="flex-1 rounded-lg border border-white/[0.1] bg-tv-void/40 py-2 text-sm text-tv-muted backdrop-blur-sm transition hover:border-tv-purple/50 hover:text-tv-fg"
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
    </motion.div>
  );
}

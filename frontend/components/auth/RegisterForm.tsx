"use client";

import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function RegisterForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const reduceMotion = useReducedMotion();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setApiKey(null);
    setPending(true);
    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name: name || undefined }),
    });
    const data = await res.json().catch(() => ({}));
    setPending(false);
    if (!res.ok) {
      const d = data.detail;
      const msg =
        typeof d === "string"
          ? d
          : Array.isArray(d) && d[0]?.msg
            ? String(d[0].msg)
            : "Registration failed";
      setError(msg);
      return;
    }
    setApiKey(data.api_key as string);
  }

  return (
    <motion.div
      className="w-full max-w-md space-y-8 rounded-2xl border border-white/[0.08] bg-tv-surface/40 p-8 shadow-2xl shadow-black/40 ring-1 ring-white/[0.06] backdrop-blur-xl"
      initial={reduceMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
    >
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight text-tv-cyan drop-shadow-[0_0_24px_rgba(34,211,238,0.25)]">
          Create account
        </h1>
        <p className="mt-1 text-sm text-tv-muted">Register via ThreatVision API</p>
      </div>

      {apiKey ? (
        <div className="space-y-4">
          <p className="text-sm text-tv-muted">Save your API key — it is shown only once.</p>
          <pre className="overflow-x-auto rounded-lg border border-white/[0.08] bg-tv-void/80 p-3 font-mono text-xs text-tv-cyan">
            {apiKey}
          </pre>
          <button
            type="button"
            onClick={() => router.push("/login")}
            className="w-full rounded-lg bg-tv-purple px-4 py-2.5 font-medium text-tv-void shadow-lg shadow-tv-purple/25 transition hover:opacity-95"
          >
            Continue to sign in
          </button>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm text-tv-muted">
              Name (optional)
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 text-tv-fg outline-none ring-tv-cyan/30 focus:border-tv-cyan/60 focus:ring-2"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm text-tv-muted">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 text-tv-fg outline-none ring-tv-cyan/30 focus:border-tv-cyan/60 focus:ring-2"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm text-tv-muted">
              Password (min 8)
            </label>
            <input
              id="password"
              type="password"
              minLength={8}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-white/[0.08] bg-tv-void/80 px-3 py-2 text-tv-fg outline-none ring-tv-cyan/30 focus:border-tv-cyan/60 focus:ring-2"
            />
          </div>
          {error && <p className="text-sm text-threat-malicious">{error}</p>}
          <button
            type="submit"
            disabled={pending}
            className="w-full rounded-lg bg-tv-cyan px-4 py-2.5 font-medium text-tv-void shadow-lg shadow-tv-cyan/20 transition hover:opacity-95 disabled:opacity-50"
          >
            {pending ? "Creating…" : "Register"}
          </button>
        </form>
      )}

      <p className="text-center text-sm text-tv-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </p>
    </motion.div>
  );
}

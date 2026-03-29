"use client";

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
      setError(typeof data.detail === "string" ? data.detail : "Registration failed");
      return;
    }
    setApiKey(data.api_key as string);
  }

  return (
    <div className="w-full max-w-md space-y-8 rounded-xl border border-tv-border bg-tv-surface p-8 shadow-lg shadow-tv-purple/5">
      <div>
        <h1 className="font-display text-2xl font-bold text-tv-cyan">Create account</h1>
        <p className="mt-1 text-sm text-tv-muted">Register via ThreatVision API</p>
      </div>

      {apiKey ? (
        <div className="space-y-4">
          <p className="text-sm text-tv-muted">Save your API key — it is shown only once.</p>
          <pre className="overflow-x-auto rounded-md border border-tv-border bg-tv-void p-3 font-mono text-xs text-tv-cyan">
            {apiKey}
          </pre>
          <button
            type="button"
            onClick={() => router.push("/login")}
            className="w-full rounded-md bg-tv-purple px-4 py-2 font-medium text-tv-void hover:opacity-90"
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
              className="mt-1 w-full rounded-md border border-tv-border bg-tv-void px-3 py-2 text-tv-fg outline-none focus:border-tv-cyan"
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
              className="mt-1 w-full rounded-md border border-tv-border bg-tv-void px-3 py-2 text-tv-fg outline-none focus:border-tv-cyan"
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
              className="mt-1 w-full rounded-md border border-tv-border bg-tv-void px-3 py-2 text-tv-fg outline-none focus:border-tv-cyan"
            />
          </div>
          {error && <p className="text-sm text-threat-malicious">{error}</p>}
          <button
            type="submit"
            disabled={pending}
            className="w-full rounded-md bg-tv-cyan px-4 py-2 font-medium text-tv-void hover:opacity-90 disabled:opacity-50"
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
    </div>
  );
}

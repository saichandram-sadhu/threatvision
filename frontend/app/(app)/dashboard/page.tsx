import { getServerSession } from "next-auth";

import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-tv-fg">Dashboard</h1>
        <p className="mt-2 max-w-2xl text-tv-muted">
          ThreatVision shell (M11). Use{" "}
          <code className="rounded bg-tv-surface px-1.5 py-0.5 font-mono text-sm text-tv-cyan">
            /api/threatvision/…
          </code>{" "}
          from the browser to reach FastAPI with your session (credentials sign-in only for now).
        </p>
      </div>
      <div className="rounded-lg border border-tv-border bg-tv-surface p-6">
        <h2 className="font-display text-lg font-semibold text-tv-purple">Session</h2>
        <dl className="mt-4 grid gap-2 font-mono text-sm">
          <div className="flex gap-2">
            <dt className="text-tv-muted">Email</dt>
            <dd>{session?.user?.email ?? "—"}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-tv-muted">Role</dt>
            <dd>{session?.user?.role ?? "—"}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-tv-muted">Backend-linked</dt>
            <dd>{linked ? "yes (UUID)" : "no (use email/password sign-in)"}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

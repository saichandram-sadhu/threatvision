import { getServerSession } from "next-auth";
import Link from "next/link";

import { AdminDashboardClient } from "@/components/admin/AdminDashboardClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function AdminPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  if (!linked) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Admin</h1>
        <p className="text-tv-muted">Sign in with email/password to use admin APIs.</p>
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  if (session?.user?.role !== "SUPERADMIN") {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Admin</h1>
        <p className="max-w-xl rounded-lg border border-threat-suspicious/40 bg-threat-suspicious/10 p-4 text-threat-suspicious">
          This area is restricted to <strong>SUPERADMIN</strong> accounts.
        </p>
        <Link href="/dashboard" className="text-tv-cyan hover:underline">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return <AdminDashboardClient />;
}

import { getServerSession } from "next-auth";
import Link from "next/link";

import { BulkAnalyzeClient } from "@/components/bulk/BulkAnalyzeClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function BulkPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  if (!linked) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Bulk analyze</h1>
        <p className="max-w-xl text-tv-muted">
          Sign in with <strong>email and password</strong> to run bulk jobs through the BFF.
        </p>
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  return <BulkAnalyzeClient />;
}

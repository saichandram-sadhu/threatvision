import { getServerSession } from "next-auth";
import Link from "next/link";

import { AnalyzePageClient } from "@/components/ioc/AnalyzePageClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function AnalyzePage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  if (!linked) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Analyze IOC</h1>
        <p className="max-w-xl text-tv-muted">
          Sign in with <strong>email and password</strong> to call the analyze API through the BFF.
        </p>
        <Link href="/login" className="text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  return <AnalyzePageClient />;
}

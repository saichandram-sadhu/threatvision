import { getServerSession } from "next-auth";
import Link from "next/link";

import { IntegrationsSettingsClient } from "@/components/settings/IntegrationsSettingsClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function IntegrationsPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  if (!linked) {
    return (
      <div className="space-y-4">
        <h1 className="font-display text-3xl font-bold text-tv-fg">Integrations</h1>
        <p className="max-w-xl text-tv-muted">
          Sign in with <strong>email and password</strong> so your session can exchange an internal JWT and load
          integration settings from the API.
        </p>
        <Link href="/login" className="inline-block text-tv-cyan hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  return <IntegrationsSettingsClient />;
}

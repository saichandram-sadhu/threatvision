import { getServerSession } from "next-auth";

import { DashboardClient } from "@/components/dashboard/DashboardClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function DashboardPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  return (
    <DashboardClient
      apiEnabled={linked}
      email={session?.user?.email ?? null}
      role={session?.user?.role ?? null}
    />
  );
}

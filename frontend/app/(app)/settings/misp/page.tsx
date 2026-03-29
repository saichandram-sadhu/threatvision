import { getServerSession } from "next-auth";

import { MispExplorerPageClient } from "@/components/settings/MispExplorerPageClient";
import { authOptions } from "@/lib/auth";
import { isBackendLinkedUserId } from "@/lib/backend";

export default async function MispExplorerPage() {
  const session = await getServerSession(authOptions);
  const linked = session?.user?.id ? isBackendLinkedUserId(session.user.id) : false;

  return <MispExplorerPageClient apiEnabled={linked} />;
}

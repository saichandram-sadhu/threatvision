import dynamic from "next/dynamic";

import { AuthGradientFallback } from "@/components/auth/AuthGradientFallback";

const NebulaBackground = dynamic(
  () => import("@/components/auth/NebulaBackground").then((m) => m.NebulaBackground),
  { ssr: false, loading: () => <AuthGradientFallback /> }
);

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-tv-void">
      <NebulaBackground />
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-4 py-12">
        {children}
      </div>
    </div>
  );
}

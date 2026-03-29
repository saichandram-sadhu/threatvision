export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-tv-void px-4 py-12">
      {children}
    </div>
  );
}

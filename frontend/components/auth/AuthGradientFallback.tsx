/**
 * Static auth backdrop for loading state and prefers-reduced-motion (no WebGL).
 */
export function AuthGradientFallback() {
  return (
    <div
      className="pointer-events-none absolute inset-0 z-0 bg-tv-void"
      style={{
        backgroundImage: [
          "radial-gradient(ellipse 90% 55% at 50% -15%, rgba(34, 211, 238, 0.16), transparent 55%)",
          "radial-gradient(ellipse 70% 45% at 100% 100%, rgba(167, 139, 250, 0.14), transparent 50%)",
          "radial-gradient(ellipse 55% 35% at 0% 85%, rgba(192, 132, 252, 0.1), transparent 45%)",
        ].join(", "),
      }}
      aria-hidden
    />
  );
}

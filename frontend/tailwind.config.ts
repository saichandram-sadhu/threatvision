import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "tv-void": "var(--tv-void)",
        "tv-surface": "var(--tv-surface)",
        "tv-border": "var(--tv-border)",
        "tv-fg": "var(--tv-fg)",
        "tv-muted": "var(--tv-muted)",
        "tv-cyan": "var(--tv-cyan)",
        "tv-purple": "var(--tv-purple)",
        "tv-accent": "var(--tv-accent)",
        "threat-malicious": "var(--threat-malicious)",
        "threat-suspicious": "var(--threat-suspicious)",
        "threat-clean": "var(--threat-clean)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-exo)", "var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "../../packages/ui/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#030712",
        "background-depth": "#05070B",
        card: "#0B0F19",
        "card-elevated": "#0F172A",
        "card-hover": "#131C31",
        border: "rgba(255, 255, 255, 0.08)",
        "border-glow": "rgba(6, 182, 212, 0.35)",
        foreground: "#FFFFFF",
        "muted-foreground": "#94A3B8",
        "subtle-foreground": "#64748B",
        brand: {
          primary: "#06B6D4",
          cyan: "#00E5FF",
          cobalt: "#1E40AF",
          accent: "#38BDF8",
        },
        status: {
          operational: "#10B981",
          triaging: "#F59E0B",
          critical: "#EF4444",
          agent: "#06B6D4",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      animation: {
        "pulse-subtle": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-slow": "glow 8s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { opacity: "0.4" },
          "100%": { opacity: "0.8" },
        },
      },
    },
  },
  plugins: [],
};

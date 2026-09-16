/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#000000",
        paper: "#FFFFFF",
        status: {
          ok: "#16A34A",
          warn: "#D97706",
          critical: "#DC2626",
          agent: "#2563EB",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      letterSpacing: { tightest: "-0.05em" },
      fontSize: {
        "f--2": ["var(--step--2)", "1.4"], "f--1": ["var(--step--1)", "1.5"], "f-0": ["var(--step-0)", "1.6"], "f-1": ["var(--step-1)", "1.55"],
        "f-2": ["var(--step-2)", "1.3"], "f-3": ["var(--step-3)", "1.15"], "f-4": ["var(--step-4)", "1.05"], "f-5": ["var(--step-5)", "1.0"],
        "f-6": ["var(--step-6)", "0.96"], "f-7": ["var(--step-7)", "0.92"],
      },
      spacing: {
        "fl-3xs": "var(--space-3xs)", "fl-2xs": "var(--space-2xs)", "fl-xs": "var(--space-xs)", "fl-s": "var(--space-s)", "fl-m": "var(--space-m)",
        "fl-l": "var(--space-l)", "fl-xl": "var(--space-xl)", "fl-2xl": "var(--space-2xl)", "fl-3xl": "var(--space-3xl)", gutter: "var(--gutter)",
      },
      maxWidth: { container: "var(--container)" },
      keyframes: {
        marquee: { "0%": { transform: "translateX(0)" }, "100%": { transform: "translateX(-50%)" } },
        rise: { "0%": { opacity: "0", transform: "translateY(24px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        shimmer: { "0%": { backgroundPosition: "200% 0" }, "100%": { backgroundPosition: "-200% 0" } },
      },
      animation: {
        marquee: "marquee 40s linear infinite",
        rise: "rise 0.9s cubic-bezier(0.16,1,0.3,1) both",
        shimmer: "shimmer 2.4s linear infinite",
      },
    },
  },
  plugins: [],
};

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
        background: "#090D16",
        card: "#0F172A",
        "card-hover": "#1E293B",
        border: "#1E293B",
        foreground: "#F8FAFC",
        "muted-foreground": "#94A3B8",
        brand: {
          primary: "#3B82F6",
        },
        status: {
          operational: "#10B981",
          triaging: "#F59E0B",
          critical: "#EF4444",
          agent: "#06B6D4",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};

import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "PARAXIS AI — The Intelligent Operational Layer for Modern Campuses",
  description: "See what is happening. Understand what matters. Coordinate what happens next. Paraxis connects campus graph context with autonomous triage and verified human-in-the-loop workflows.",
  keywords: ["campus operations", "intelligent operations", "campus graph", "incident management", "operational intelligence"],
  openGraph: {
    title: "PARAXIS AI — The Intelligent Operational Layer for Modern Campuses",
    description: "See what is happening. Understand what matters. Coordinate what happens next.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-background font-sans text-foreground selection:bg-brand-cyan/20 selection:text-brand-cyan">
        {children}
      </body>
    </html>
  );
}

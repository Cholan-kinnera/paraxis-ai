import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Paraxis AI — Intelligent Operational Layer",
  description: "See what is happening. Understand what matters. Coordinate what happens next.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}

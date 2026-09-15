import React from "react";
import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { CommandCenter } from "@/components/landing/CommandCenter";
import { ProblemStatement } from "@/components/landing/ProblemStatement";
import { OperationalGraph } from "@/components/landing/OperationalGraph";
import { CapabilitiesBento } from "@/components/landing/CapabilitiesBento";
import { NorthStarWorkflow } from "@/components/landing/NorthStarWorkflow";
import { GovernanceSection } from "@/components/landing/GovernanceSection";
import { FinalCTA } from "@/components/landing/FinalCTA";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-background text-foreground selection:bg-brand-cyan/20 selection:text-brand-cyan overflow-x-hidden">
      {/* 1. Floating Pill Navigation */}
      <Navbar />

      <main id="main-content">
        {/* 2. Hero Section: Display Typography & Atmospheric Illumination */}
        <Hero />

        {/* 3. Live Operations Command Center: High-Density Product UI */}
        <CommandCenter />

        {/* 4. Problem Statement: Generous Whitespace & Editorial Transition (Zero Cards) */}
        <ProblemStatement />

        {/* 5. Campus Operational Graph: Living Hierarchy & Incident Traversal */}
        <OperationalGraph />

        {/* 6. Product Capabilities: 4 Asymmetrical Bento Cards with Custom SVG Visuals */}
        <CapabilitiesBento />

        {/* 7. North-Star Workflow: 6-Stage Signal-to-Resolution Journey */}
        <NorthStarWorkflow />

        {/* 8. Enterprise Governance: High-Trust Human-in-the-Loop & Policy Gates */}
        <GovernanceSection />

        {/* 9. Final Call to Action: Typographic Crescendo & Action Pill */}
        <FinalCTA />
      </main>

      {/* 10. Monochromatic Institutional Footer */}
      <Footer />
    </div>
  );
}

"use client";
import dynamic from "next/dynamic";
import { Navbar } from "./Navbar";
import { Hero } from "./Hero";
import { Features } from "./Features";
import { Showcase } from "./Showcase";
import { Governance } from "./Governance";
import { Proof } from "./Proof";
import { Pricing } from "./Pricing";
import { FinalCTA } from "./Footer";

const SceneCanvas = dynamic(() => import("./3d/SceneCanvas"), { ssr: false });

export function Landing() {
  return (
    <div className="noise relative min-h-screen overflow-x-clip bg-black text-white">
      <SceneCanvas />
      <Navbar />
      <main className="relative">
        <Hero />
        <Features />
        <Showcase />
        <Governance />
        <Proof />
        <Pricing />
      </main>
      <FinalCTA />
    </div>
  );
}

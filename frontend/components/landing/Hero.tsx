"use client";

import React from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { PillButton } from "./ui/PillButton";
import { StatusBadge } from "./ui/StatusBadge";
import { ArrowDown, Radio } from "lucide-react";

// Client-only dynamic import of the 3D Campus Canvas (zero SSR hydration mismatch)
const HeroCampusCanvas = dynamic(
  () => import("./3d/HeroCampusCanvas"),
  {
    ssr: false,
    loading: () => (
      <div
        className="absolute inset-0 w-full h-full bg-[#030712] pointer-events-none -z-10"
        aria-hidden="true"
      />
    ),
  }
);

export function Hero() {
  return (
    <section className="relative min-h-[92vh] lg:min-h-screen flex flex-col justify-between pt-28 pb-14 px-4 sm:px-6 lg:px-10 overflow-hidden">
      {/* Genuine Three.js / R3F 3D Campus Operational Environment */}
      <HeroCampusCanvas />

      {/* Atmospheric Vignette & Soft Gradient Mesh for Depth Separation */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_0%,_#030712_82%)] -z-10"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-24 right-0 w-[500px] h-[500px] rounded-full bg-[radial-gradient(circle,_rgba(0,229,255,0.08)_0%,_transparent_70%)] blur-[100px] -z-10"
      />

      {/* Top Telemetry Kicker */}
      <div className="max-w-7xl mx-auto w-full pt-4">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950/70 border border-white/[0.1] backdrop-blur-md shadow-sm"
        >
          <StatusBadge variant="agent" pulse={true} className="border-0 bg-transparent px-0 py-0 text-[11px]">
            ✦ LIVE CAMPUS OPERATIONAL LAYER
          </StatusBadge>
          <span className="text-white/20">•</span>
          <span className="text-xs text-slate-300 font-mono">Engineering Campus · AP-204 Active</span>
        </motion.div>
      </div>

      {/* Primary Asymmetrical Editorial Hero Composition */}
      <div className="max-w-7xl mx-auto w-full my-auto py-12 sm:py-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-end">
          {/* Left Column: Huge Editorial Display Headline */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-7"
          >
            <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-medium tracking-[-0.035em] text-white leading-[1.05] mb-6">
              Unify campus
              <br />
              operations with
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-cyan-300">
                PARAXIS AI.
              </span>
            </h1>

            {/* Institutional Trust Indicators */}
            <div className="flex items-center gap-4 pt-2">
              <div className="flex -space-x-2 overflow-hidden">
                <div className="inline-block h-7 w-7 rounded-full ring-2 ring-[#030712] bg-slate-800 flex items-center justify-center text-[10px] font-mono text-cyan-300">
                  AP
                </div>
                <div className="inline-block h-7 w-7 rounded-full ring-2 ring-[#030712] bg-slate-700 flex items-center justify-center text-[10px] font-mono text-slate-200">
                  EN
                </div>
                <div className="inline-block h-7 w-7 rounded-full ring-2 ring-[#030712] bg-slate-800 flex items-center justify-center text-[10px] font-mono text-indigo-300">
                  CS
                </div>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Validated on Paraxis Demo Campus
              </span>
            </div>
          </motion.div>

          {/* Right Column: Mission Promise & Dual Action Pills */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-5 flex flex-col items-start lg:items-end justify-end space-y-6"
          >
            <div className="p-5 rounded-2xl bg-slate-950/60 border border-white/[0.08] backdrop-blur-md max-w-md">
              <div className="text-xs font-mono uppercase text-brand-cyan tracking-wider mb-2 flex items-center gap-2">
                <Radio className="h-3 w-3 animate-pulse text-brand-cyan" />
                OPERATIONAL PROMISE
              </div>
              <p className="text-sm sm:text-base text-slate-300 font-light leading-relaxed mb-3">
                See what is happening. Understand what matters. Coordinate what happens next.
              </p>
              <p className="text-xs text-slate-400 font-light leading-relaxed">
                Paraxis sits above campus systems to ingest operational signals, contextualize events through the campus graph, and coordinate verified remediation.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
              <PillButton href="#command-center" variant="primary" size="lg">
                Explore Paraxis
              </PillButton>
              <PillButton href="#operational-graph" variant="secondary" size="lg" icon={false}>
                View Telemetry ▷
              </PillButton>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Bottom Visual Bridge to Live Command Center */}
      <div className="max-w-7xl mx-auto w-full flex items-center justify-between pt-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-cyan animate-ping" />
          <span>REAL-TIME 3D TOPOLOGY ACTIVE</span>
        </div>

        <a
          href="#command-center"
          className="inline-flex items-center gap-2 text-[11px] font-mono text-slate-400 hover:text-white transition-colors group focus:outline-none"
          aria-label="Scroll to live operations command center"
        >
          <span>COMMAND CENTER</span>
          <ArrowDown className="h-3.5 w-3.5 text-brand-cyan group-hover:translate-y-0.5 transition-transform" />
        </a>
      </div>
    </section>
  );
}

"use client";

import React from "react";
import { motion } from "framer-motion";
import { PillButton } from "./ui/PillButton";

export function FinalCTA() {
  return (
    <section className="relative py-32 sm:py-40 lg:py-44 px-4 sm:px-6 lg:px-8 text-center overflow-hidden">
      {/* Cinematic ambient background glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-[radial-gradient(circle,_rgba(6,182,212,0.18)_0%,_rgba(30,64,175,0.08)_50%,_transparent_75%)] blur-[100px] -z-10"
      />

      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="mb-6"
        >
          <span className="text-xs font-mono tracking-[0.25em] uppercase text-cyan-400/80 font-medium">
            ENTERPRISE CAMPUS DEPLOYMENT
          </span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 22 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-medium tracking-[-0.035em] text-white leading-tight mb-8"
        >
          Deploy the Intelligent{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-cyan-300">
            Operational Layer.
          </span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg text-slate-400 font-light max-w-xl mx-auto leading-relaxed mb-12"
        >
          See every event, understand operational significance, and coordinate remediation across your physical and administrative campus graph.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <PillButton href="#command-center" variant="primary" size="lg">
            Explore Paraxis
          </PillButton>
          <PillButton href="#workflow" variant="secondary" size="lg" icon={false}>
            See the operational workflow ▷
          </PillButton>
        </motion.div>
      </div>
    </section>
  );
}

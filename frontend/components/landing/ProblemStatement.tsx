"use client";

import React from "react";
import { motion } from "framer-motion";

export function ProblemStatement() {
  return (
    <section className="relative py-32 sm:py-40 lg:py-48 px-4 sm:px-6 lg:px-8 text-center overflow-hidden">
      {/* Deep atmospheric backdrop glow */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-[radial-gradient(ellipse_at_center,_rgba(30,64,175,0.08)_0%,_transparent_70%)] blur-[90px] -z-10"
      />

      <div className="max-w-4xl mx-auto">
        {/* Editorial Sub-kicker */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mb-6"
        >
          <span className="text-xs font-mono tracking-[0.25em] uppercase text-cyan-400/80">
            THE OPERATIONAL IMPERATIVE
          </span>
        </motion.div>

        {/* Large Editorial Headline */}
        <motion.h2
          initial={{ opacity: 0, y: 22 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="text-3xl sm:text-5xl lg:text-6xl font-normal tracking-[-0.03em] text-white leading-[1.14] mb-8"
        >
          Campuses run on dozens of fragmented systems.{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-200 to-slate-400">
            Paraxis turns operational noise into clear, coordinated action.
          </span>
        </motion.h2>

        {/* Quiet editorial supporting text */}
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-base sm:text-lg text-slate-400 font-light max-w-2xl mx-auto leading-relaxed"
        >
          Instead of replacing sovereign university systems, Paraxis acts as the overarching intelligence tier — ingesting unstructured reports, resolving context via the campus graph, and coordinating verified remediation.
        </motion.p>
      </div>
    </section>
  );
}

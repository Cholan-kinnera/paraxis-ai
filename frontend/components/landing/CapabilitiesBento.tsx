"use client";

import React from "react";
import { motion } from "framer-motion";
import { Users, Utensils, Wrench, Shield, TrendingDown } from "lucide-react";

export function CapabilitiesBento() {
  return (
    <section
      id="capabilities"
      className="relative w-full bg-[#F3F4F6] text-slate-900 py-24 sm:py-32 border-y border-slate-300/60"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Editorial Section Header with Light Gallery Stone Treatment */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 pb-8 border-b border-slate-300 gap-6">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.6 }}
              className="mb-3"
            >
              <span className="text-xs font-mono uppercase tracking-[0.25em] text-slate-500 font-semibold">
                ABOUT THE PLATFORM
              </span>
            </motion.div>

            <motion.h2
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-3xl sm:text-4xl lg:text-5xl font-normal tracking-[-0.03em] text-slate-950 leading-tight"
            >
              Core Operational Pillars
            </motion.h2>
          </div>

          <motion.p
            initial={{ opacity: 0, y: 14 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-sm sm:text-base text-slate-600 font-light max-w-md leading-relaxed"
          >
            Paraxis delivers a unified operational graph, transforming fragmented signals across diverse campus verticals into coordinated, verifiable action.
          </motion.p>
        </div>

        {/* 4 Architectural Gallery Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* 1. Smart Attendance */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6 }}
            className="p-8 sm:p-10 rounded-2xl bg-white border border-slate-200/90 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.05)] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-700 px-2.5 py-1 rounded-full bg-cyan-50 border border-cyan-200 font-medium">
                  Signal Analysis
                </span>
                <Users className="h-5 w-5 text-slate-400" />
              </div>

              <h3 className="text-2xl font-medium text-slate-900 tracking-tight mb-3">
                Smart Attendance
              </h3>
              <p className="text-sm text-slate-600 font-light leading-relaxed mb-8">
                Evaluates section-level attendance trends, identifies systemic cohort absence anomalies, and triggers non-punitive advisor check-in workflows. Strictly workflow signals and anomaly detection — zero biometric or facial recognition.
              </p>
            </div>

            {/* Bespoke Dark Metallic Micro-Visual */}
            <div className="rounded-xl bg-[#0B0F19] text-white border border-slate-800 p-5 font-mono shadow-inner">
              <div className="flex justify-between items-center text-xs mb-3">
                <span className="text-slate-400">Course Section CS-301</span>
                <span className="text-amber-400 flex items-center gap-1 text-[11px]">
                  <TrendingDown className="h-3 w-3" />
                  32% Drop Flagged
                </span>
              </div>
              <svg viewBox="0 0 400 80" className="w-full h-16 overflow-visible" aria-label="Attendance trendline">
                <path
                  d="M 0 25 Q 70 20 140 28 T 260 22 L 290 65 L 340 50 L 400 45"
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="2.5"
                />
                <circle cx="290" cy="65" r="4.5" fill="#F59E0B" />
                <line x1="290" y1="10" x2="290" y2="65" stroke="#F59E0B" strokeDasharray="3 3" />
                <text x="295" y="22" fill="#F59E0B" fontSize="10">
                  Anomaly Trigger
                </text>
              </svg>
              <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
                <span>Signal: Section-Level Deviation</span>
                <span className="text-cyan-400 font-medium">Advisor Notice Cleared</span>
              </div>
            </div>
          </motion.div>

          {/* 2. Hostel & Mess Operations */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="p-8 sm:p-10 rounded-2xl bg-white border border-slate-200/90 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.05)] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-emerald-700 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 font-medium">
                  Resource Planning
                </span>
                <Utensils className="h-5 w-5 text-slate-400" />
              </div>

              <h3 className="text-2xl font-medium text-slate-900 tracking-tight mb-3">
                Hostel & Mess Operations
              </h3>
              <p className="text-sm text-slate-600 font-light leading-relaxed mb-8">
                Aligns meal demand forecasts with physical check-in volume, preempts dining waste, and coordinates kitchen inventory replenishment before shortages occur.
              </p>
            </div>

            {/* Bespoke Dark Metallic Micro-Visual: Forecast vs Actual Volume */}
            <div className="rounded-xl bg-[#0B0F19] text-white border border-slate-800 p-5 font-mono shadow-inner">
              <div className="flex justify-between items-center text-xs mb-3">
                <span className="text-slate-400">Breakfast Service Forecast</span>
                <span className="text-emerald-400 text-[11px]">-26% Waste Delta</span>
              </div>
              <div className="grid grid-cols-4 gap-2 pt-1 pb-3">
                <div>
                  <div className="text-[10px] text-slate-400 mb-1">Block A</div>
                  <div className="h-10 bg-white/[0.05] rounded flex items-end p-0.5 gap-0.5">
                    <div className="w-1/2 bg-slate-600 h-[80%] rounded-sm" title="Forecast" />
                    <div className="w-1/2 bg-emerald-400 h-[78%] rounded-sm" title="Actual" />
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 mb-1">Block B</div>
                  <div className="h-10 bg-white/[0.05] rounded flex items-end p-0.5 gap-0.5">
                    <div className="w-1/2 bg-slate-600 h-[95%] rounded-sm" />
                    <div className="w-1/2 bg-emerald-400 h-[92%] rounded-sm" />
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 mb-1">Block C</div>
                  <div className="h-10 bg-white/[0.05] rounded flex items-end p-0.5 gap-0.5">
                    <div className="w-1/2 bg-slate-600 h-[60%] rounded-sm" />
                    <div className="w-1/2 bg-emerald-400 h-[62%] rounded-sm" />
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 mb-1">Block D</div>
                  <div className="h-10 bg-white/[0.05] rounded flex items-end p-0.5 gap-0.5">
                    <div className="w-1/2 bg-slate-600 h-[75%] rounded-sm" />
                    <div className="w-1/2 bg-emerald-400 h-[74%] rounded-sm" />
                  </div>
                </div>
              </div>
              <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
                <span>Predicted: 1,420 Meals</span>
                <span className="text-emerald-400 font-medium">Variance: 3.8%</span>
              </div>
            </div>
          </motion.div>

          {/* 3. AI Campus Maintenance */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="p-8 sm:p-10 rounded-2xl bg-white border border-slate-200/90 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.05)] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-cyan-700 px-2.5 py-1 rounded-full bg-cyan-50 border border-cyan-200 font-medium">
                  Predictive Facilities
                </span>
                <Wrench className="h-5 w-5 text-slate-400" />
              </div>

              <h3 className="text-2xl font-medium text-slate-900 tracking-tight mb-3">
                AI Campus Maintenance
              </h3>
              <p className="text-sm text-slate-600 font-light leading-relaxed mb-8">
                Ingests HVAC compressor telemetry, backup power runtime signals, and plumbing pressure anomalies to assign preventative work orders before system failure.
              </p>
            </div>

            {/* Bespoke Dark Metallic Micro-Visual: Compressor Health */}
            <div className="rounded-xl bg-[#0B0F19] text-white border border-slate-800 p-5 font-mono shadow-inner">
              <div className="flex justify-between items-center text-xs mb-3">
                <span className="text-slate-400">Library Central HVAC Unit</span>
                <span className="text-cyan-400 text-[11px]">Telemetry Normal</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <div className="flex items-center gap-3">
                  <div className="relative h-10 w-10 flex items-center justify-center">
                    <svg className="h-10 w-10 -rotate-90">
                      <circle cx="20" cy="20" r="16" stroke="rgba(255,255,255,0.15)" strokeWidth="3" fill="none" />
                      <circle
                        cx="20"
                        cy="20"
                        r="16"
                        stroke="#00E5FF"
                        strokeWidth="3"
                        strokeDasharray="100"
                        strokeDashoffset="18"
                        fill="none"
                      />
                    </svg>
                    <span className="text-[10px] text-white font-medium absolute">82%</span>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-200">Compressor Load</div>
                    <div className="text-[10px] text-slate-400">22.4 kWh Active</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] text-emerald-400">Preventative OK</div>
                  <div className="text-[10px] text-slate-400">Next cycle in 48h</div>
                </div>
              </div>
              <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
                <span>14 Early Interventions</span>
                <span className="text-emerald-400 font-medium">Zero Unscheduled Halts</span>
              </div>
            </div>
          </motion.div>

          {/* 4. Safety & Trust */}
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="p-8 sm:p-10 rounded-2xl bg-white border border-slate-200/90 shadow-[0_4px_24px_-4px_rgba(0,0,0,0.05)] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-mono uppercase tracking-wider text-rose-700 px-2.5 py-1 rounded-full bg-rose-50 border border-rose-200 font-medium">
                  Confidential Routing
                </span>
                <Shield className="h-5 w-5 text-slate-400" />
              </div>

              <h3 className="text-2xl font-medium text-slate-900 tracking-tight mb-3">
                Safety & Trust
              </h3>
              <p className="text-sm text-slate-600 font-light leading-relaxed mb-8">
                Enables secure, anonymous concern intake with zero existence leakage, automated risk evaluation, and immediate confidential security escalation.
              </p>
            </div>

            {/* Bespoke Dark Metallic Micro-Visual: Encrypted Reporter Pipeline */}
            <div className="rounded-xl bg-[#0B0F19] text-white border border-slate-800 p-5 font-mono shadow-inner">
              <div className="flex justify-between items-center text-xs mb-3">
                <span className="text-slate-400">Confidential Signal Pipeline</span>
                <span className="text-emerald-400 text-[11px]">E2E Scoped</span>
              </div>
              <div className="flex items-center justify-between py-2 text-xs">
                <div className="px-3 py-1.5 rounded bg-white/[0.05] border border-white/[0.1] text-slate-200 text-center">
                  <div className="text-[10px] text-slate-400">INTAKE</div>
                  <span>Anonymous</span>
                </div>
                <span className="text-cyan-400/80">→ [Encrypted Gate] →</span>
                <div className="px-3 py-1.5 rounded bg-cyan-950/60 border border-cyan-500/40 text-cyan-200 text-center">
                  <div className="text-[10px] text-cyan-400">DISPATCH</div>
                  <span>Duty Officer</span>
                </div>
              </div>
              <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-[11px] text-slate-400">
                <span>Identity Isolated</span>
                <span className="text-cyan-400 font-medium">Escalation: &lt; 3m</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}

"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./ui/GlassCard";
import { StatusBadge } from "./ui/StatusBadge";
import {
  LIVE_OPERATIONS_METRICS,
  PRIMARY_DEMO_INCIDENT,
} from "@/lib/landing-data";
import {
  Wifi,
  Clock,
  Radio,
  MapPin,
  CheckCircle2,
  Users,
  Activity,
  Layers,
  Sparkles,
  Smartphone,
  Globe,
  GraduationCap,
} from "lucide-react";

export function CommandCenter() {
  const [activeTab, setActiveTab] = useState<"cluster" | "telemetry">("cluster");
  const incident = PRIMARY_DEMO_INCIDENT;

  return (
    <section
      id="command-center"
      className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-24"
    >
      {/* Subtle radial aura behind the console card */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl h-[450px] bg-[radial-gradient(ellipse_at_center,_rgba(6,182,212,0.12)_0%,_transparent_60%)] blur-[80px] -z-10"
      />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <GlassCard
          elevated={true}
          className="p-4 sm:p-6 lg:p-8 border-white/[0.12] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.9)] overflow-hidden"
        >
          {/* Top Console Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-white/[0.08] gap-4">
            <div className="flex items-center gap-3">
              <div className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_#10B981]" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs uppercase tracking-widest text-brand-cyan">
                    PARAXIS DEMO CAMPUS
                  </span>
                  <span className="text-white/20">•</span>
                  <span className="text-xs text-slate-400 font-mono">Live Operations Console</span>
                </div>
                <h2 className="text-sm sm:text-base font-medium text-white tracking-tight">
                  Engineering Campus · Infrastructure Operations
                </h2>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08]">
                <Radio className="h-3 w-3 text-brand-cyan animate-pulse" />
                Active Incident Triage
              </span>
              <span className="hidden sm:inline-block text-white/20">•</span>
              <span className="hidden sm:inline-block">14:32:08 UTC</span>
            </div>
          </div>

          {/* Top Metric Strip (4 Pillars) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-8">
            {LIVE_OPERATIONS_METRICS.map((metric, idx) => (
              <div
                key={metric.label}
                className="p-4 rounded-xl bg-[#070B14]/60 border border-white/[0.06] hover:border-white/15 transition-colors"
              >
                <div className="text-xs font-mono text-slate-400 mb-1">{metric.label}</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-semibold tracking-tight text-white">
                    {metric.value}
                  </span>
                  {metric.change && (
                    <span
                      className={`text-xs font-mono ${
                        metric.changeType === "urgent"
                          ? "text-rose-400"
                          : metric.changeType === "positive"
                          ? "text-emerald-400"
                          : "text-slate-400"
                      }`}
                    >
                      {metric.change}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 truncate mt-1">{metric.detail}</div>
              </div>
            ))}
          </div>

          {/* Main Operational Incident Showcase */}
          <div className="rounded-xl bg-[#050811]/80 border border-white/[0.08] p-5 sm:p-7">
            {/* Incident Header & Clustering Banner */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-6 mb-6 border-b border-white/[0.06] gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-rose-500/15 border border-rose-500/30 text-rose-300 font-mono text-xs font-medium">
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                    PRIORITY: HIGH
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/10 text-slate-300 font-mono text-xs">
                    {incident.category}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/[0.05] border border-white/10 text-slate-300 font-mono text-xs flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-brand-cyan" />
                    {incident.building} · {incident.floor}
                  </span>
                </div>
                <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight flex items-center gap-2.5">
                  <Wifi className="h-5 w-5 text-brand-cyan shrink-0" />
                  {incident.title}
                </h3>
              </div>

              {/* Intelligent Clustering Indicator */}
              <div className="flex items-center gap-3 bg-brand-cyan/[0.06] border border-brand-cyan/25 rounded-xl px-4 py-2.5">
                <div className="h-8 w-8 rounded-lg bg-brand-cyan/20 flex items-center justify-center text-brand-cyan shrink-0">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-medium text-white">
                    Intelligently Clustered Incident
                  </div>
                  <div className="text-xs text-brand-cyan font-mono">
                    7 reports → 1 shared incident (Portal 4 · Mobile 2 · Faculty Desk 1)
                  </div>
                </div>
              </div>
            </div>

            {/* Incident Operational Context Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Context Details & Clustered Reports (7 cols) */}
              <div className="lg:col-span-7 flex flex-col justify-between">
                {/* Specific Location & Asset Details */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                    <span className="text-slate-500 block mb-1 text-[11px]">LOCATION NODE</span>
                    <span className="text-slate-200 font-medium">{incident.room}</span>
                  </div>
                  <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                    <span className="text-slate-500 block mb-1 text-[11px]">ASSOCIATED ASSET</span>
                    <span className="text-slate-200 font-medium">{incident.asset}</span>
                  </div>
                  <div className="col-span-2 sm:col-span-1 p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                    <span className="text-slate-500 block mb-1 text-[11px]">ASSIGNED DISPATCH</span>
                    <span className="text-emerald-400 font-medium flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {incident.assignedTeam}
                    </span>
                  </div>
                </div>

                {/* Sub-Tabs: Clustered Signals vs Live Telemetry */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setActiveTab("cluster")}
                        className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-colors min-h-[36px] ${
                          activeTab === "cluster"
                            ? "bg-white/[0.08] text-white border-white/20"
                            : "text-slate-400 border-transparent hover:text-slate-200"
                        }`}
                      >
                        Clustered Signals ({incident.clusterCount})
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveTab("telemetry")}
                        className={`text-xs font-mono px-3 py-1.5 rounded-lg border transition-colors min-h-[36px] ${
                          activeTab === "telemetry"
                            ? "bg-white/[0.08] text-white border-white/20"
                            : "text-slate-400 border-transparent hover:text-slate-200"
                        }`}
                      >
                        Signal Anomaly Curve
                      </button>
                    </div>

                    <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">
                      Source Graph Linked
                    </span>
                  </div>

                  {activeTab === "cluster" ? (
                    <div className="space-y-2 max-h-[190px] overflow-y-auto pr-1">
                      {incident.clusterReports.slice(0, 4).map((report) => (
                        <div
                          key={report.id}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] text-xs hover:border-white/10 transition-colors"
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            {report.source === "Mobile App" ? (
                              <Smartphone className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                            ) : report.source === "Portal" ? (
                              <Globe className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                            ) : (
                              <GraduationCap className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                            )}
                            <span className="text-slate-300 truncate">{report.summary}</span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0 font-mono text-[11px] text-slate-500 ml-2">
                            <span>{report.reporterRole}</span>
                            <span>•</span>
                            <span>{report.timestamp}</span>
                          </div>
                        </div>
                      ))}
                      <div className="text-center pt-1">
                        <span className="text-[11px] font-mono text-brand-cyan/80">
                          + 3 additional correlated signals merged into this record
                        </span>
                      </div>
                    </div>
                  ) : (
                    /* SVG Telemetry Signal Curve */
                    <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                      <div className="flex justify-between items-center text-[11px] font-mono text-slate-400 mb-2">
                        <span>AP-204 Packet Telemetry (Last 60m)</span>
                        <span className="text-rose-400">Packet Drop Spike @ 14:15</span>
                      </div>
                      <svg
                        viewBox="0 0 500 120"
                        className="w-full h-24 overflow-visible"
                        aria-label="AP-204 throughput anomaly telemetry chart"
                      >
                        <defs>
                          <linearGradient id="curveGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.3" />
                            <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                        {/* Threshold reference line */}
                        <line
                          x1="0"
                          y1="60"
                          x2="500"
                          y2="60"
                          stroke="rgba(255,255,255,0.1)"
                          strokeDasharray="4 4"
                        />
                        {/* Fill area */}
                        <path
                          d="M 0 30 Q 80 32 150 35 T 230 38 L 260 105 L 300 110 L 340 70 L 420 40 L 500 35 L 500 120 L 0 120 Z"
                          fill="url(#curveGradient)"
                        />
                        {/* Line path */}
                        <path
                          d="M 0 30 Q 80 32 150 35 T 230 38 L 260 105 L 300 110 L 340 70 L 420 40 L 500 35"
                          fill="none"
                          stroke="#00E5FF"
                          strokeWidth="2"
                        />
                        {/* Anomaly drop marker */}
                        <circle cx="280" cy="108" r="4" fill="#EF4444" />
                        <text x="290" y="112" fill="#EF4444" fontSize="10" fontFamily="monospace">
                          Drop: 0% Throughput
                        </text>
                      </svg>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Operational Lifecycle Stepper & SLA (5 cols) */}
              <div className="lg:col-span-5 flex flex-col justify-between p-4 sm:p-5 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-mono text-slate-400">OPERATIONAL LIFECYCLE</span>
                    <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      SLA: 42m remaining
                    </span>
                  </div>

                  {/* Vertical Operational Stepper */}
                  <div className="space-y-3 relative pl-3 border-l border-white/10 ml-2">
                    {incident.lifecycleSteps.map((step) => {
                      const isCompleted = step.state === "completed";
                      const isActive = step.state === "active";
                      return (
                        <div key={step.name} className="relative group">
                          {/* Dot indicator */}
                          <div
                            className={`absolute -left-[19px] top-1 h-3 w-3 rounded-full border ${
                              isCompleted
                                ? "bg-emerald-400 border-emerald-500"
                                : isActive
                                ? "bg-brand-cyan border-cyan-400 animate-ping"
                                : "bg-slate-800 border-slate-700"
                            }`}
                          />
                          {isActive && (
                            <div className="absolute -left-[19px] top-1 h-3 w-3 rounded-full bg-brand-cyan border border-cyan-400" />
                          )}

                          <div className="flex items-baseline justify-between text-xs">
                            <span
                              className={`font-mono font-medium ${
                                isCompleted
                                  ? "text-slate-300"
                                  : isActive
                                  ? "text-brand-cyan font-semibold"
                                  : "text-slate-500"
                              }`}
                            >
                              {step.name}
                            </span>
                            {step.timestamp && (
                              <span className="text-[11px] font-mono text-slate-500">
                                {step.timestamp}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-400 font-light mt-0.5 leading-snug">
                            {step.detail}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Bottom SLA Countdown Indicator */}
                <div className="mt-5 pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-amber-400" />
                    <span className="font-mono text-slate-300 text-[11px]">
                      SLA Target: 60m Max
                    </span>
                  </div>
                  <span className="font-mono text-emerald-400 font-medium">
                    Remediation on track
                  </span>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </section>
  );
}

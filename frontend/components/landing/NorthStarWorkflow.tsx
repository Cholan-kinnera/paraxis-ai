"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./ui/GlassCard";
import { NORTH_STAR_WORKFLOW, WorkflowStage } from "@/lib/landing-data";
import {
  FileText,
  Sparkles,
  AlertTriangle,
  Send,
  Clock,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";

export function NorthStarWorkflow() {
  const [activeStepIndex, setActiveStepIndex] = useState<number>(3); // Default on ASSIGN
  const activeStage: WorkflowStage = NORTH_STAR_WORKFLOW[activeStepIndex];

  const getStepIcon = (index: number) => {
    switch (index) {
      case 0:
        return <FileText className="h-4 w-4" />;
      case 1:
        return <Sparkles className="h-4 w-4" />;
      case 2:
        return <AlertTriangle className="h-4 w-4" />;
      case 3:
        return <Send className="h-4 w-4" />;
      case 4:
        return <Clock className="h-4 w-4" />;
      case 5:
        return <CheckCircle2 className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <section id="workflow" className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
      {/* Editorial Section Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="mb-4"
        >
          <span className="text-xs font-mono uppercase tracking-[0.25em] text-cyan-400/80">
            NORTH-STAR JOURNEY
          </span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-3xl sm:text-4xl lg:text-5xl font-normal tracking-[-0.03em] text-white leading-tight mb-6"
        >
          From Signal to Resolution
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg text-slate-400 font-light leading-relaxed"
        >
          Follow an operational event through Paraxis — from raw, unstructured student reports to autonomous clustering, policy authorization, and verified closure.
        </motion.p>
      </div>

      {/* Interactive Horizontal Workflow Bar (Desktop) & Step List */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.8 }}
      >
        <GlassCard elevated={true} className="p-6 sm:p-8 lg:p-10 border-white/[0.12]">
          {/* Step Pill Selector */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3 mb-10">
            {NORTH_STAR_WORKFLOW.map((stage, idx) => {
              const isSelected = activeStepIndex === idx;
              const isPassed = idx < activeStepIndex;

              return (
                <button
                  key={stage.step}
                  type="button"
                  onClick={() => setActiveStepIndex(idx)}
                  className={`flex flex-col items-start p-3 sm:p-4 rounded-xl border text-left transition-all duration-300 focus:outline-none min-h-[44px] ${
                    isSelected
                      ? "bg-brand-cyan/[0.14] border-brand-cyan/70 shadow-[0_0_20px_-3px_rgba(6,182,212,0.3)] text-white"
                      : isPassed
                      ? "bg-white/[0.03] border-white/10 text-slate-300 hover:border-white/20"
                      : "bg-white/[0.01] border-white/[0.04] text-slate-500 hover:text-slate-300 hover:border-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <span className="font-mono text-xs text-brand-cyan font-bold">
                      {stage.step}
                    </span>
                    <div
                      className={`p-1 rounded-md ${
                        isSelected ? "text-brand-cyan bg-brand-cyan/20" : "text-slate-500"
                      }`}
                    >
                      {getStepIcon(idx)}
                    </div>
                  </div>
                  <div className="font-semibold text-xs sm:text-sm tracking-tight mb-0.5">
                    {stage.title}
                  </div>
                  <div className="text-[11px] font-mono text-slate-400 truncate w-full">
                    {stage.subtitle}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Detailed Stage Deep-Dive Card */}
          <div className="rounded-2xl bg-[#050811]/95 border border-brand-cyan/30 p-6 sm:p-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-6 border-b border-white/[0.08] gap-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-brand-cyan/20 border border-brand-cyan/40 flex items-center justify-center text-brand-cyan">
                  {getStepIcon(activeStepIndex)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs uppercase text-brand-cyan">
                      STAGE {activeStage.step} OF 06
                    </span>
                    <span className="text-white/20">•</span>
                    <span className="text-xs text-slate-400 font-mono">{activeStage.subtitle}</span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
                    {activeStage.title}
                  </h3>
                </div>
              </div>

              <span className="px-3.5 py-1.5 rounded-full bg-brand-cyan/[0.1] border border-brand-cyan/30 text-brand-cyan font-mono text-xs self-start sm:self-auto">
                {activeStage.stateBadge}
              </span>
            </div>

            {/* Narrative Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                  OPERATIONAL EVENT
                </span>
                <p className="text-sm sm:text-base text-slate-200 font-light leading-relaxed">
                  {activeStage.actionSummary}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-brand-cyan/[0.03] border border-brand-cyan/15">
                <span className="text-xs font-mono uppercase tracking-wider text-brand-cyan block mb-2">
                  PARAXIS INTELLIGENCE ACTION
                </span>
                <p className="text-sm sm:text-base text-slate-300 font-light leading-relaxed">
                  {activeStage.systemAction}
                </p>
              </div>
            </div>

            {/* Bottom Stepper Progress Bar */}
            <div className="mt-8 pt-6 border-t border-white/[0.06] flex items-center justify-between text-xs font-mono text-slate-500">
              <div className="flex items-center gap-2">
                <span>Demonstrating: Wi-Fi Access Point AP-204</span>
                <span>•</span>
                <span className="text-slate-400">Engineering Block, Floor 2</span>
              </div>
              <div className="flex items-center gap-1.5 text-brand-cyan">
                <span>Step {activeStepIndex + 1}/6</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </section>
  );
}

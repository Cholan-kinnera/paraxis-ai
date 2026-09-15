"use client";

import React from "react";
import { motion } from "framer-motion";
import { GlassCard } from "./ui/GlassCard";
import { GOVERNANCE_PILLARS } from "@/lib/landing-data";
import { ShieldCheck, UserCheck, Scale, FileCode2 } from "lucide-react";

export function GovernanceSection() {
  const getPillarIcon = (idx: number) => {
    switch (idx) {
      case 0:
        return <ShieldCheck className="h-5 w-5 text-emerald-400" />;
      case 1:
        return <UserCheck className="h-5 w-5 text-brand-cyan" />;
      case 2:
        return <Scale className="h-5 w-5 text-amber-400" />;
      case 3:
        return <FileCode2 className="h-5 w-5 text-cyan-300" />;
      default:
        return <ShieldCheck className="h-5 w-5 text-slate-400" />;
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case "ALLOW":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "REQUIRE_HUMAN_APPROVAL":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "DENY":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "AUDIT":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      default:
        return "bg-white/10 text-slate-300 border-white/10";
    }
  };

  return (
    <section id="governance" className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28">
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
            ENTERPRISE GOVERNANCE & SOVEREIGNTY
          </span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-3xl sm:text-4xl lg:text-5xl font-normal tracking-[-0.03em] text-white leading-tight mb-6"
        >
          AI Coordinates. Humans Remain in Control.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg text-slate-400 font-light leading-relaxed"
        >
          The artificial intelligence layer never serves as the sovereign source of truth. The AI proposes, the policy engine authorizes, and campus administrators retain full approval authority.
        </motion.p>
      </div>

      {/* 4-Quadrant Architecture Layout with Hairline Crosshairs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {GOVERNANCE_PILLARS.map((pillar, idx) => (
          <motion.div
            key={pillar.title}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.6, delay: idx * 0.1 }}
          >
            <GlassCard className="p-6 sm:p-8 flex flex-col justify-between h-full border-white/[0.08] hover:border-white/20 transition-all duration-300">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-white/[0.04] border border-white/[0.06]">
                    {getPillarIcon(idx)}
                  </div>
                  <span
                    className={`text-xs font-mono px-2.5 py-1 rounded-full border ${getActionBadgeColor(
                      pillar.policyAction
                    )}`}
                  >
                    {pillar.policyAction}
                  </span>
                </div>

                <span className="text-xs font-mono uppercase tracking-wider text-slate-500 block mb-1">
                  {pillar.tagline}
                </span>
                <h3 className="text-xl font-semibold text-white tracking-tight mb-3">
                  {pillar.title}
                </h3>
                <p className="text-sm text-slate-400 font-light leading-relaxed mb-6">
                  {pillar.description}
                </p>
              </div>

              <div className="pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs font-mono text-slate-400">
                <span className="text-slate-500 text-[11px]">Enforcement Rule</span>
                <span className="text-slate-300 truncate max-w-[240px] text-right">
                  {pillar.ruleSnippet}
                </span>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { GlassCard } from "./ui/GlassCard";
import { StatusBadge } from "./ui/StatusBadge";
import { GRAPH_HIERARCHY_DEMO } from "@/lib/landing-data";
import {
  Network,
  Building2,
  Layers,
  DoorClosed,
  Cpu,
  Wifi,
  Users,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";

// Client-only dynamic import of the 3D Operational Graph Canvas
const OperationalGraphCanvas = dynamic(
  () => import("./3d/OperationalGraphCanvas"),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[420px] sm:h-[500px] lg:h-[540px] rounded-2xl bg-[#030712]/90 border border-white/[0.08] flex items-center justify-center">
        <div className="text-xs font-mono text-slate-500 animate-pulse">
          INITIALIZING 3D TOPOLOGY CANVAS...
        </div>
      </div>
    ),
  }
);

export function OperationalGraph() {
  const [selectedNode, setSelectedNode] = useState<string>("ast");

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "organization":
        return <ShieldCheck className="h-4 w-4 text-emerald-400" />;
      case "campus":
        return <Network className="h-4 w-4 text-brand-cyan" />;
      case "department":
        return <Users className="h-4 w-4 text-cyan-300" />;
      case "building":
        return <Building2 className="h-4 w-4 text-slate-300" />;
      case "floor":
        return <Layers className="h-4 w-4 text-slate-400" />;
      case "room":
        return <DoorClosed className="h-4 w-4 text-slate-400" />;
      case "asset":
        return <Cpu className="h-4 w-4 text-brand-cyan" />;
      default:
        return <Network className="h-4 w-4 text-slate-400" />;
    }
  };

  return (
    <section
      id="operational-graph"
      className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 sm:py-28"
    >
      {/* Section Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="mb-4"
        >
          <span className="text-xs font-mono uppercase tracking-[0.25em] text-cyan-400/80">
            THE CORE DIFFERENTIATOR
          </span>
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-3xl sm:text-4xl lg:text-5xl font-normal tracking-[-0.03em] text-white leading-tight mb-6"
        >
          The Campus Operational Graph
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-lg text-slate-400 font-light leading-relaxed"
        >
          Paraxis maintains a living topology of every institutional tier. When an issue is reported, it doesn&apos;t float as an orphaned ticket — it anchors directly into the physical and operational hierarchy.
        </motion.p>
      </div>

      {/* Main Interactive Spatial Graph Presentation */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.8 }}
      >
        <GlassCard elevated={true} className="p-6 sm:p-8 lg:p-10 border-white/[0.12]">
          {/* Top Operational Context Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-8 border-b border-white/[0.08] gap-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono uppercase tracking-widest text-slate-400">
                ACTIVE GRAPH TOPOLOGY
              </span>
              <span className="text-white/20">•</span>
              <span className="text-xs text-brand-cyan font-mono">
                7 Connected Operational Tiers
              </span>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge variant="agent">Genuine 3D Traversal</StatusBadge>
            </div>
          </div>

          {/* Genuine 3D Spatial Scene Container */}
          <div className="mb-8">
            <OperationalGraphCanvas
              selectedNodeId={selectedNode}
              onSelectNode={(nodeId) => setSelectedNode(nodeId)}
            />
          </div>

          {/* Node Hierarchy Strip (Synced with 3D Scene) */}
          <div className="relative mb-10">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.06]">
              <span className="text-xs font-mono text-slate-400">
                HIERARCHY ANCESTRY TRAVERSAL (CLICK TO HIGHLIGHT 3D NODE)
              </span>
              <button
                type="button"
                onClick={() => setSelectedNode("ast")}
                className="inline-flex items-center gap-1.5 text-[11px] font-mono text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                <RotateCcw className="h-3 w-3" />
                <span>Focus AP-204</span>
              </button>
            </div>

            <div className="overflow-x-auto pb-4 pt-1 -mx-2 px-2">
              <div className="flex items-center justify-between min-w-[720px] gap-2">
                {GRAPH_HIERARCHY_DEMO.map((node, idx) => {
                  const isSelected = selectedNode === node.id;
                  const isAffected = node.status === "affected" || node.status === "active-remediation";

                  return (
                    <React.Fragment key={node.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedNode(node.id)}
                        className={`flex flex-col items-start p-3.5 rounded-xl border text-left transition-all duration-300 min-w-[130px] sm:min-w-[145px] focus:outline-none ${
                          isSelected
                            ? "bg-brand-cyan/[0.12] border-brand-cyan/60 shadow-[0_0_20px_-3px_rgba(6,182,212,0.3)]"
                            : isAffected
                            ? "bg-white/[0.03] border-brand-cyan/25 hover:border-brand-cyan/40"
                            : "bg-white/[0.02] border-white/[0.06] hover:border-white/15"
                        }`}
                      >
                        <div className="flex items-center justify-between w-full mb-2">
                          <div className="p-1.5 rounded-md bg-white/[0.04]">
                            {getNodeIcon(node.type)}
                          </div>
                          <span className="text-[10px] font-mono uppercase text-slate-500">
                            {node.type}
                          </span>
                        </div>
                        <div className="text-xs font-medium text-white truncate w-full mb-0.5">
                          {node.label}
                        </div>
                        <div className="text-[10px] font-mono text-slate-400 truncate w-full">
                          {node.sublabel}
                        </div>
                      </button>

                      {idx < GRAPH_HIERARCHY_DEMO.length - 1 && (
                        <div className="shrink-0 flex items-center px-1">
                          <ArrowRight className="h-3.5 w-3.5 text-brand-cyan/40" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Incident Attachment Walkthrough Card */}
          <div className="rounded-xl bg-[#050811]/90 border border-brand-cyan/20 p-5 sm:p-7">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between pb-4 mb-6 border-b border-white/[0.06] gap-3">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-brand-cyan block mb-1">
                  GRAPH TRAVERSAL EXAMPLE
                </span>
                <h3 className="text-lg sm:text-xl font-semibold text-white tracking-tight flex items-center gap-2">
                  <Wifi className="h-4 w-4 text-brand-cyan" />
                  Resolving Student Signal to Physical & Operational Ancestry
                </h3>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
                Context Resolved in 12ms
              </span>
            </div>

            {/* Tree Resolution Breadcrumb */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono text-xs mb-6">
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                <span className="text-slate-500 block text-[10px]">1. SIGNAL INTAKE</span>
                <span className="text-slate-200 font-medium truncate block">
                  Wi-Fi Outage Report
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                <span className="text-slate-500 block text-[10px]">2. CAMPUS GRAPH NODE</span>
                <span className="text-slate-200 font-medium truncate block">
                  Engineering Campus
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                <span className="text-slate-500 block text-[10px]">3. SPATIAL ANCESTRY</span>
                <span className="text-slate-200 font-medium truncate block">
                  Eng Block · Floor 2 · Rm 101
                </span>
              </div>
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                <span className="text-cyan-300 font-medium truncate block">
                  Access Point AP-204
                </span>
              </div>
              <div className="p-3 rounded-lg bg-emerald-500/[0.05] border border-emerald-500/20">
                <span className="text-emerald-500 block text-[10px]">5. OWNING TEAM</span>
                <span className="text-emerald-400 font-medium truncate block">
                  Network Operations
                </span>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-slate-400 font-light leading-relaxed">
              Because the Access Point is authoritatively mapped to Room 101 on Floor 2 of the Engineering Block, Paraxis eliminates ambiguous back-and-forth communication. The incident is instantly assigned to Network Operations with full location ancestry attached.
            </p>
          </div>
        </GlassCard>
      </motion.div>
    </section>
  );
}

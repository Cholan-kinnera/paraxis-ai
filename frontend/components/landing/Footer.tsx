import React from "react";
import Link from "next/link";
import { StatusBadge } from "./ui/StatusBadge";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.08] bg-[#02040A] text-slate-400 py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-white/[0.06]">
          {/* Brand Col */}
          <div className="md:col-span-2">
            <Link href="#" className="flex items-center gap-2.5 mb-4 group inline-block">
              <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-brand-cyan/20 to-brand-cobalt/40 border border-brand-cyan/40 flex items-center justify-center text-xs font-mono font-bold text-white group-hover:border-brand-cyan transition-colors">
                PX
              </div>
              <span className="font-semibold tracking-wider text-sm text-white flex items-center gap-1.5">
                PARAXIS <span className="text-brand-cyan text-xs font-mono">AI</span>
              </span>
            </Link>
            <p className="text-sm text-slate-400 font-light max-w-sm mb-6 leading-relaxed">
              The Intelligent Operational Layer for Modern Campuses. See what is happening. Understand what matters. Coordinate what happens next.
            </p>
            <div className="flex items-center gap-2">
              <StatusBadge variant="operational" pulse={true}>
                Campus Operational Layer Online
              </StatusBadge>
            </div>
          </div>

          {/* Links Col 1 */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-300 mb-4">
              Architecture
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm font-light">
              <li>
                <Link href="#operational-graph" className="hover:text-white transition-colors">
                  Campus Operational Graph
                </Link>
              </li>
              <li>
                <Link href="#capabilities" className="hover:text-white transition-colors">
                  Operational Capabilities
                </Link>
              </li>
              <li>
                <Link href="#workflow" className="hover:text-white transition-colors">
                  Signal to Resolution
                </Link>
              </li>
              <li>
                <Link href="#governance" className="hover:text-white transition-colors">
                  Deterministic Policy Engine
                </Link>
              </li>
            </ul>
          </div>

          {/* Links Col 2 */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-300 mb-4">
              Governance & Trust
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm font-light">
              <li>
                <Link href="#governance" className="hover:text-white transition-colors">
                  Tenant Isolation Invariant
                </Link>
              </li>
              <li>
                <Link href="#governance" className="hover:text-white transition-colors">
                  Role-Based Access Control
                </Link>
              </li>
              <li>
                <Link href="#governance" className="hover:text-white transition-colors">
                  Human-in-the-Loop Gates
                </Link>
              </li>
              <li>
                <Link href="#governance" className="hover:text-white transition-colors">
                  Immutable Auditability
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-500">
          <div>
            © {new Date().getFullYear()} Paraxis AI. The Intelligent Operational Layer for Modern Campuses.
          </div>
          <div className="flex items-center gap-4">
            <span>Production Foundation v0.3.0</span>
            <span>•</span>
            <span className="text-slate-400">Enterprise Ready</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

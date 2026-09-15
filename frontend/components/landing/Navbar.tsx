"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { PillButton } from "./ui/PillButton";
import { StatusBadge } from "./ui/StatusBadge";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Platform", href: "#command-center" },
    { label: "Graph", href: "#operational-graph" },
    { label: "Pillars", href: "#capabilities" },
    { label: "Workflow", href: "#workflow" },
    { label: "Governance", href: "#governance" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-4 pt-4 sm:pt-6 transition-all duration-300">
      <nav
        aria-label="Main Navigation"
        className={`w-full max-w-6xl flex items-center justify-between px-4 sm:px-6 py-2.5 rounded-full border transition-all duration-300 ${
          scrolled
            ? "bg-[#030712]/90 backdrop-blur-xl border-white/[0.12] shadow-[0_10px_30px_-10px_rgba(0,0,0,0.8)]"
            : "bg-[#0B0F19]/60 backdrop-blur-lg border-white/[0.08]"
        }`}
      >
        {/* Brand mark */}
        <Link href="#" className="flex items-center gap-2.5 group focus:outline-none">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-brand-cyan/20 to-brand-cobalt/40 border border-brand-cyan/40 flex items-center justify-center text-xs font-mono font-bold text-white group-hover:border-brand-cyan transition-colors">
            PX
          </div>
          <span className="font-semibold tracking-wider text-sm text-white flex items-center gap-1.5">
            PARAXIS <span className="text-brand-cyan text-xs font-mono">AI</span>
          </span>
        </Link>

        {/* Center links (Desktop) */}
        <div className="hidden md:flex items-center gap-1 lg:gap-2">
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-xs lg:text-sm text-slate-300 hover:text-white px-3 py-1.5 rounded-full hover:bg-white/[0.06] transition-colors font-medium"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right CTA */}
        <div className="hidden sm:flex items-center gap-3">
          <StatusBadge variant="operational" pulse={true} className="hidden lg:inline-flex">
            Live Console
          </StatusBadge>
          <PillButton href="#command-center" variant="primary" size="sm" icon={true}>
            Explore Console
          </PillButton>
        </div>

        {/* Mobile menu button */}
        <div className="flex sm:hidden items-center gap-2">
          <PillButton href="#command-center" variant="primary" size="sm" icon={false}>
            Console
          </PillButton>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-full text-slate-300 hover:text-white hover:bg-white/[0.08] focus:outline-none min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Navigation Dropdown */}
      {mobileMenuOpen && (
        <div
          className="sm:hidden fixed inset-x-4 top-20 bg-[#0B0F19]/95 backdrop-blur-2xl border border-white/10 rounded-2xl p-5 shadow-2xl flex flex-col gap-3"
          role="dialog"
          aria-label="Mobile menu"
        >
          {navLinks.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm text-slate-200 hover:text-brand-cyan py-2.5 px-3 rounded-lg hover:bg-white/[0.05] transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 border-t border-white/10 flex justify-between items-center">
            <StatusBadge variant="operational">Operations Active</StatusBadge>
            <PillButton href="#command-center" variant="primary" size="sm" onClick={() => setMobileMenuOpen(false)}>
              Explore Console ↗
            </PillButton>
          </div>
        </div>
      )}
    </header>
  );
}

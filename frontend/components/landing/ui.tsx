"use client";
import Link from "next/link";
import { motion, type HTMLMotionProps } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

const ease = [0.16, 1, 0.3, 1] as const;

export function Reveal({ children, delay = 0, className, ...rest }: HTMLMotionProps<"div"> & { delay?: number }) {
  return (
    <motion.div initial={{ opacity: 0, y: 28 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-12% 0px" }} transition={{ duration: 0.9, ease, delay }} className={className} {...rest}>
      {children}
    </motion.div>
  );
}

/** Page container: fluid gutters, capped width. */
export const Container = ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={cn("mx-auto w-full max-w-container", className)}>{children}</div>;

export function Pill({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("inline-flex items-center gap-2 rounded-full glass px-fl-s py-fl-3xs text-f--2 font-medium text-white/80", className)}>{children}</span>;
}

/** Reference-style pill button: label + circular arrow badge. */
export function Button({ href, children, variant = "primary", className }: { href: string; children: React.ReactNode; variant?: "primary" | "ghost"; className?: string }) {
  return (
    <Link href={href} className={cn("group pointer-events-auto inline-flex items-center gap-2.5 rounded-full py-[0.45rem] pl-[1.15rem] pr-[0.45rem] text-f--1 font-medium transition-all duration-300", variant === "primary" ? "bg-white text-black hover:shadow-[0_0_3rem_-0.5rem_rgba(255,255,255,0.7)]" : "text-white hover:bg-white/[0.06]", className)}>
      {children}
      <span className={cn("grid h-[1.75rem] w-[1.75rem] place-items-center rounded-full transition-transform duration-300 group-hover:rotate-45", variant === "primary" ? "bg-black text-white" : "bg-white text-black")}><ArrowUpRight className="h-3.5 w-3.5" strokeWidth={2.2} /></span>
    </Link>
  );
}

export function SectionHead({ eyebrow, title, sub, align = "center" }: { eyebrow?: string; title: React.ReactNode; sub?: string; align?: "center" | "left" }) {
  return (
    <div className={cn("max-w-[48rem]", align === "center" ? "mx-auto text-center" : "")}>
      {eyebrow && <Reveal><span className="font-mono text-f--2 uppercase tracking-[0.25em] text-white/45">{eyebrow}</span></Reveal>}
      <Reveal delay={0.05}><h2 className="mt-fl-xs text-balance text-f-5 font-medium tracking-tightest text-white">{title}</h2></Reveal>
      {sub && <Reveal delay={0.1}><p className={cn("mt-fl-s text-balance text-f-0 text-white/55", align === "center" ? "mx-auto max-w-[36rem]" : "max-w-[36rem]")}>{sub}</p></Reveal>}
    </div>
  );
}

export function GlassCard({ children, className, hover = true }: { children: React.ReactNode; className?: string; hover?: boolean }) {
  return (
    <div className={cn("group/card pointer-events-auto relative overflow-hidden rounded-[1.5rem] border border-white/[0.08] bg-white/[0.025] p-fl-m backdrop-blur-xl transition-all duration-500", hover && "hover:border-white/20 hover:bg-white/[0.045]", className)}>
      <div className="pointer-events-none absolute -top-24 left-1/2 h-48 w-[120%] -translate-x-1/2 rounded-full bg-white/[0.06] blur-3xl opacity-0 transition-opacity duration-700 group-hover/card:opacity-100" />
      <div className="relative">{children}</div>
    </div>
  );
}

export const Serif = ({ children }: { children: React.ReactNode }) => <em className="font-serif italic tracking-normal text-white/90">{children}</em>;

"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Menu, X, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/Logo";

const links = [{ href: "#product", label: "Product" }, { href: "#platform", label: "Platform" }, { href: "#pricing", label: "Pricing" }];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  useEffect(() => { const f = () => setScrolled(window.scrollY > 24); f(); window.addEventListener("scroll", f, { passive: true }); return () => window.removeEventListener("scroll", f); }, []);
  return (
    <header className="pointer-events-none fixed inset-x-0 top-0 z-50 px-gutter pt-fl-s">
      <div className="relative mx-auto flex max-w-container items-center justify-between">
        <Link href="/" className="pointer-events-auto flex items-center gap-2.5 text-white"><Logo className="h-[1.6rem] w-[1.6rem]" /><span className="text-f-0 font-semibold tracking-tight">Paraxis<span className="text-white/50"> AI</span></span></Link>
        <nav className={cn("pointer-events-auto absolute left-1/2 hidden -translate-x-1/2 items-center rounded-full p-1 pl-2 transition-all duration-500 md:flex", scrolled ? "glass-strong" : "bg-white/[0.02]")}>
          {links.map((l) => <a key={l.href} href={l.href} className="rounded-full px-fl-s py-[0.55rem] text-f--1 text-white/70 transition-colors hover:text-white">{l.label}</a>)}
          <Link href="/login" className="group ml-1 inline-flex items-center gap-2 rounded-full bg-white py-[0.4rem] pl-4 pr-1.5 text-f--1 font-medium text-black">Get Started<span className="grid h-6 w-6 place-items-center rounded-full bg-black text-white transition-transform group-hover:rotate-45"><ArrowUpRight className="h-3 w-3" strokeWidth={2.4} /></span></Link>
        </nav>
        <Link href="/login" className="pointer-events-auto hidden text-f--1 text-white/70 transition-colors hover:text-white md:block">Sign in</Link>
        <button onClick={() => setOpen((o) => !o)} aria-label="Menu" className="pointer-events-auto grid h-10 w-10 place-items-center rounded-full glass text-white md:hidden">{open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}</button>
      </div>
      {open && (
        <div className="pointer-events-auto mx-auto mt-3 max-w-container rounded-[1.5rem] glass-strong p-3 md:hidden">
          {links.map((l) => <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="block rounded-2xl px-4 py-3 text-f-0 text-white/80">{l.label}</a>)}
          <div className="mt-2 grid grid-cols-2 gap-2 border-t border-white/10 pt-3">
            <Link href="/login" className="rounded-full glass py-3 text-center text-f--1 text-white">Sign in</Link>
            <Link href="/login" className="rounded-full bg-white py-3 text-center text-f--1 font-medium text-black">Get Started</Link>
          </div>
        </div>
      )}
    </header>
  );
}

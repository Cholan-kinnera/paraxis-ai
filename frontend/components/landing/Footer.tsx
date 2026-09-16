"use client";
import Link from "next/link";
import { Button, Container, Reveal, Serif } from "./ui";
import { Logo } from "@/components/Logo";

const Social = ({ d, label }: { d: string; label: string }) => (
  <a href="#" aria-label={label} className="pointer-events-auto grid h-10 w-10 place-items-center rounded-full text-white/70 transition-colors hover:bg-white/10 hover:text-white"><svg viewBox="0 0 24 24" className="h-[1.1rem] w-[1.1rem]" fill="currentColor"><path d={d} /></svg></a>
);
const icons = {
  linkedin: "M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.36V9h3.41v1.56h.05c.47-.9 1.63-1.85 3.36-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 20.45H3.56V9h3.56v11.45z",
  x: "M18.9 2H22l-7.2 8.26L23.3 22h-6.6l-5.2-6.8L5.6 22H2.5l7.7-8.8L1.6 2h6.8l4.7 6.2L18.9 2zm-1.1 18.1h1.7L7.3 3.8H5.4l12.4 16.3z",
  github: "M12 .5A11.5 11.5 0 0 0 .5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.2.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.9 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.2c0 .3.2.7.8.6A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z",
};

/** Final CTA + footer as one full-viewport section, like the reference: centred headline, socials, copyright bottom-left; the vortex sits on the right. */
export function FinalCTA() {
  return (
    <section id="final" className="pointer-events-none relative z-10 flex min-h-[100svh] flex-col px-gutter pb-fl-m pt-fl-3xl">
      <Container className="flex flex-1 flex-col items-center justify-center text-center">
        <Reveal><h2 className="max-w-[12ch] text-balance text-[length:clamp(2.6rem,1.2rem+5.6vw,6.75rem)] font-medium leading-[0.95] tracking-tightest text-white">Launch with <Serif>Paraxis.</Serif></h2></Reveal>
        <Reveal delay={0.1}><p className="mx-auto mt-fl-m max-w-[34rem] text-f-0 text-white/55">See what is happening. Understand what matters. Coordinate what happens next.</p></Reveal>
        <Reveal delay={0.2} className="mt-fl-l flex flex-col items-center gap-2 sm:flex-row"><Button href="/login" variant="ghost">Get Started</Button><Button href="#product">Learn More</Button></Reveal>
        <Reveal delay={0.3} className="mt-fl-l flex items-center gap-1"><Social d={icons.linkedin} label="LinkedIn" /><Social d={icons.github} label="GitHub" /><Social d={icons.x} label="X" /></Reveal>
      </Container>
      <Container className="flex flex-col gap-fl-xs border-t border-white/[0.08] pt-fl-s font-mono text-f--2 uppercase tracking-[0.18em] text-white/40 sm:flex-row sm:items-center sm:justify-between">
        <span className="flex items-center gap-2"><Logo className="h-4 w-4 text-white/70" />© {new Date().getFullYear()} — Paraxis AI. All rights reserved.</span>
        <nav className="pointer-events-auto flex flex-wrap gap-fl-s">{["Product", "Security", "Docs", "Contact"].map((l) => <Link key={l} href="/login" className="transition-colors hover:text-white">{l}</Link>)}</nav>
      </Container>
    </section>
  );
}

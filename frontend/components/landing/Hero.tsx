"use client";
import { motion } from "framer-motion";
import { Pill, Button, Serif, Container } from "./ui";

const ease = [0.16, 1, 0.3, 1] as const;
const up = (d: number) => ({ initial: { opacity: 0, y: 28 }, animate: { opacity: 1, y: 0 }, transition: { duration: 1.1, ease, delay: d } });

export function Hero() {
  return (
    <section id="hero" className="pointer-events-none relative z-10 flex min-h-[100svh] flex-col px-gutter pb-fl-3xl pt-[clamp(6rem,4rem+8vh,9rem)]">
      <Container className="flex flex-col items-center text-center">
        <motion.div {...up(0.1)}><Pill>Now with Autonomous Triage</Pill></motion.div>
        <motion.h1 {...up(0.25)} className="mt-fl-m max-w-[14ch] text-balance text-[length:clamp(2.6rem,1.2rem+5.6vw,6.75rem)] font-medium leading-[0.95] tracking-tightest text-white">
          Turn Reports Into <Serif>Resolutions.</Serif>
        </motion.h1>
        <motion.p {...up(0.4)} className="mt-fl-m max-w-[38rem] text-balance text-f-0 text-white/60">
          Ingest messy campus reports, understand what matters, and coordinate verified action across every department — powered by governed AI agents.
        </motion.p>
        <motion.div {...up(0.55)} id="hero-cta" className="mt-fl-l flex flex-col items-center gap-3 sm:flex-row">
          <Button href="/login">Get Started</Button>
          <Button href="#product" variant="ghost">See It in Action</Button>
        </motion.div>
      </Container>
    </section>
  );
}

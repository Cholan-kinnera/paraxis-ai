"use client";
import { ShieldCheck, Network, Gauge } from "lucide-react";
import { Container, GlassCard, Reveal, SectionHead, Serif } from "./ui";

const items = [
  { icon: Network, title: "Contextual Intelligence", body: "Every report is grounded in your campus graph — building, floor, room, asset — before an agent proposes a single action." },
  { icon: ShieldCheck, title: "Deterministic Governance", body: "Every consequential action passes a policy gate: allow, deny, or require human approval. The LLM is never the source of truth." },
  { icon: Gauge, title: "Ready to Scale", body: "Multi-tenant by design. Organizations, campuses, departments and SLAs — isolated, auditable, and fast under load." },
];

export function Features() {
  return (
    <section id="product" className="pointer-events-none relative z-10 px-gutter py-fl-3xl">
      <Container>
        <SectionHead title={<>Your all-in-one <Serif>operations</Serif> engine.</>} sub="Context, governance, and coordination — everything you need to run a modern campus, zero chaos." />
        <div className="mt-fl-xl grid gap-fl-xs md:grid-cols-3">
          {items.map((it, i) => (
            <Reveal key={it.title} delay={i * 0.08}>
              <GlassCard className="flex h-full min-h-[18rem] flex-col">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-black"><it.icon className="h-5 w-5" strokeWidth={1.8} /></div>
                <h3 className="mt-auto pt-fl-l text-f-2 font-medium tracking-tight text-white">{it.title}</h3>
                <p className="mt-fl-2xs text-f--1 text-white/55">{it.body}</p>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

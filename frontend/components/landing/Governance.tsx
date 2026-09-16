"use client";
import { Lock, Layers, FileCheck, Globe } from "lucide-react";
import { Container, GlassCard, Reveal, SectionHead, Serif } from "./ui";

const items = [
  { icon: Lock, title: "Tenant-Scoped Everything", body: "Every query, every vector search, every tool call is scoped to organization and campus from the security token — never from the client." },
  { icon: Layers, title: "Typed Tools Only", body: "Agents act through registered, typed tools. No raw SQL, no shell, no open network egress. Ever." },
  { icon: FileCheck, title: "Immutable Audit Trail", body: "Append-only event timelines for incidents and tasks. Who did what, when, and why — with correlation IDs end-to-end." },
  { icon: Globe, title: "Human-in-the-Loop Gates", body: "Financial, disciplinary, and public-communication actions pause for explicit approval. Rejections are recorded, not lost." },
];

export function Governance() {
  return (
    <section id="governance" className="pointer-events-none relative z-10 px-gutter py-fl-3xl">
      <Container>
        <SectionHead title={<>Rock-solid <Serif>governance,</Serif> everywhere.</>} sub="Stay protected and coordinated with deterministic policy checks and full auditability — no surprises, no compromises." />
        <div className="mt-fl-xl grid gap-fl-xs sm:grid-cols-2 lg:grid-cols-4">
          {items.map((it, i) => (
            <Reveal key={it.title} delay={i * 0.06}>
              <GlassCard className="flex h-full min-h-[16rem] flex-col">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-white text-black"><it.icon className="h-5 w-5" strokeWidth={1.8} /></div>
                <h3 className="mt-auto pt-fl-l text-f-1 font-medium tracking-tight text-white">{it.title}</h3>
                <p className="mt-fl-2xs text-f--1 text-white/55">{it.body}</p>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

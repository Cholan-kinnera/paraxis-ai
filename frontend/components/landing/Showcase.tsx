"use client";
import { cn } from "@/lib/utils";
import { Button, Container, Reveal, Serif } from "./ui";
import { EvidenceFrame, ReportFrame, GraphFrame } from "./Frames";

const rows = [
  { id: "platform", eyebrow: "Agent Copilot", title: <>Your AI Copilot, <Serif>Always Ready</Serif></>, body: "Meet your operational co-pilot. It resolves entities, detects duplicates, scores priority, and proposes the next action — with evidence, never a black box.", cta: "Discover How", frame: EvidenceFrame },
  { id: "report", eyebrow: "Natural-Language Ingestion", title: <>Report Now, <Serif>Resolve Faster</Serif></>, body: "“Wi-Fi is down in Block B, Room 204.” That’s all it takes. Paraxis links the report to AP-04, clusters related reports, and dispatches IT with an SLA already ticking.", cta: "See It Work", frame: ReportFrame, flip: true },
  { id: "workflow", eyebrow: "Cross-Functional Coordination", title: <>Connect Every <Serif>Department</Serif></>, body: "IT, facilities, hostel, safety — one living operational graph. Tasks flow to the right team, escalate on breach, and close only after the reporter verifies the fix.", cta: "Try It Now", frame: GraphFrame },
];

export function Showcase() {
  return (
    <section className="pointer-events-none relative z-10 px-gutter py-fl-2xl">
      <Container className="flex flex-col gap-fl-3xl">
        {rows.map((r) => (
          <div key={r.id} id={r.id} className={cn("grid items-center gap-fl-xl lg:grid-cols-2 lg:gap-fl-3xl", r.flip && "lg:[&>*:first-child]:order-2")}>
            <div className="max-w-[34rem]">
              <Reveal><span className="font-mono text-f--2 uppercase tracking-[0.25em] text-white/45">{r.eyebrow}</span></Reveal>
              <Reveal delay={0.05}><h2 className="mt-fl-xs text-balance text-f-5 font-medium tracking-tightest text-white">{r.title}</h2></Reveal>
              <Reveal delay={0.1}><p className="mt-fl-s text-f-0 text-white/55">{r.body}</p></Reveal>
              <Reveal delay={0.15} className="mt-fl-m"><Button href="/login">{r.cta}</Button></Reveal>
            </div>
            <Reveal delay={0.1}><r.frame /></Reveal>
          </div>
        ))}
      </Container>
    </section>
  );
}

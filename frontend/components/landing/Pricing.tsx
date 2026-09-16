"use client";
import { Sparkle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button, Container, GlassCard, Reveal, SectionHead, Serif } from "./ui";

const plans = [
  { n: "Starter", p: "Free", d: "Kick off with core features for a single campus.", f: ["Up to 3 operators", "Essential command center", "Basic incident & task flows", "Reporter portal", "1 GB evidence storage"] },
  { n: "Pro", p: "$49", per: "/month", d: "More power for growing campuses ready to move faster.", f: ["Up to 10 operators", "Advanced command center", "Priority SLA workflows", "Agent copilot & approvals", "50 GB evidence storage"], hot: true },
  { n: "Enterprise", p: "$149", per: "/month", d: "All features unlocked plus dedicated support.", f: ["Unlimited operators", "Full analytics & pattern insights", "Automated escalation workflows", "Dedicated success manager", "1 TB evidence storage"] },
];

export function Pricing() {
  return (
    <section id="pricing" className="pointer-events-none relative z-10 px-gutter py-fl-3xl">
      <Container>
        <SectionHead title={<>Plans that <Serif>grow</Serif> with you.</>} sub="Flexible pricing for campuses of every size and stage. Upgrade, downgrade, or cancel anytime." />
        <div className="mt-fl-xl grid gap-fl-xs md:grid-cols-3">
          {plans.map((pl, i) => (
            <Reveal key={pl.n} delay={i * 0.08}>
              <GlassCard className={cn("flex h-full flex-col", pl.hot && "border-white/25 bg-[radial-gradient(120%_80%_at_50%_0%,rgba(255,255,255,0.14),rgba(255,255,255,0.02)_60%)]")}>
                <h3 className="text-f-2 font-medium text-white">{pl.n}</h3>
                <p className="mt-1 text-f--1 text-white/50">{pl.d}</p>
                <div className="mt-fl-l flex items-baseline gap-1"><span className="text-f-5 font-medium tracking-tightest text-white">{pl.p}</span>{pl.per && <span className="text-f-0 text-white/45">{pl.per}</span>}</div>
                <ul className="mt-fl-l flex-1 space-y-fl-2xs">{pl.f.map((f) => <li key={f} className="flex items-center gap-3 text-f--1 text-white/75"><Sparkle className="h-3.5 w-3.5 shrink-0 fill-white text-white" />{f}</li>)}</ul>
                <div className="mt-fl-l"><Button href="/login" variant={pl.hot ? "primary" : "ghost"} className={cn(!pl.hot && "border border-white/15")}>Learn More</Button></div>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

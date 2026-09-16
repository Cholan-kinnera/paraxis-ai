"use client";
import { Container, GlassCard, Reveal, SectionHead, Serif } from "./ui";

const logos = ["Apex University", "Meridian Institute", "Northgate College", "Helios Polytechnic", "Orbit Campus", "Vanta School of Engineering"];
const quotes = [
  { n: "Alex Chen", r: "Head of Campus Operations", q: "Switching to Paraxis cut our manual triage in half. Reports land on the right technician with an SLA already running — we closed more tickets in a week than the previous month." },
  { n: "Priya Das", r: "Dean of Student Affairs", q: "Finally, a system that feels smart but stays accountable. Every agent decision comes with evidence, and nothing public goes out without a human saying yes." },
  { n: "Daniel Rivera", r: "CIO", q: "It plugged right into our stack, kept tenant data isolated, and gave us an audit trail our security team actually likes. Recurring failures surfaced in the first week." },
];
const stats = [["99.98%", "Always On, Always Reliable"], ["12 min", "Median Time to Dispatch"], ["24/7", "Real Humans, Real Approvals"]];

export function Proof() {
  return (
    <section id="proof" className="pointer-events-none relative z-10 px-gutter py-fl-3xl">
      <Container>
        <SectionHead title={<>Trusted by <Serif>leading</Serif> campuses.</>} sub="Operations teams across universities and institutes already coordinate with Paraxis." />
        <Reveal className="mask-fade-x mt-fl-xl overflow-hidden">
          <div className="flex w-max animate-marquee gap-fl-2xl whitespace-nowrap">
            {[...logos, ...logos].map((l, i) => <span key={i} className="font-serif text-f-3 italic text-white/40">{l}</span>)}
          </div>
        </Reveal>

        <div className="mt-fl-3xl">
          <SectionHead title={<>See what our <Serif>clients</Serif> love</>} sub="Discover why teams trust Paraxis to coordinate workflows, protect students, and deliver standout campus experiences." />
          <div className="mt-fl-xl grid gap-fl-xs md:grid-cols-3">
            {quotes.map((t, i) => (
              <Reveal key={t.n} delay={i * 0.08}>
                <GlassCard className="flex h-full flex-col">
                  <div className="flex items-center gap-3">
                    <div className="grid h-11 w-11 place-items-center rounded-full border border-white/15 bg-white/[0.06] font-mono text-f--2 text-white">{t.n.split(" ").map((s) => s[0]).join("")}</div>
                    <div><div className="text-f--1 font-medium text-white">{t.n}</div><div className="text-f--2 text-white/45">{t.r}</div></div>
                  </div>
                  <p className="mt-fl-m text-f--1 text-white/70">“{t.q}”</p>
                </GlassCard>
              </Reveal>
            ))}
          </div>
        </div>

        {/* the sphere returns behind these — see stage.ts */}
        <div id="stats" className="mt-fl-3xl grid gap-fl-xs sm:grid-cols-3">
          {stats.map(([v, l], i) => (
            <Reveal key={v} delay={i * 0.08}>
              <GlassCard hover={false} className="bg-black/50 backdrop-blur-xl">
                <div className="text-f-5 font-medium tracking-tightest text-white">{v}</div>
                <div className="mt-fl-2xs text-f--1 text-white/60">{l}</div>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

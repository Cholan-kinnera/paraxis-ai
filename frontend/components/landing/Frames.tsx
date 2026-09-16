"use client";
import { CheckCircle2, MapPin, Cpu, Copy, ShieldCheck, Wifi, Zap, Droplets, Flame } from "lucide-react";
import { cn } from "@/lib/utils";

function Frame({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("pointer-events-auto relative rounded-[1.6rem] glass-strong p-2 shadow-[0_40px_120px_-40px_rgba(255,255,255,0.15)]", className)}>
      <div className="absolute inset-x-12 -top-px h-px bg-gradient-to-r from-transparent via-white/60 to-transparent" />
      <div className="rounded-[1.25rem] border border-white/[0.06] bg-black/60 p-5 text-white sm:p-6">{children}</div>
    </div>
  );
}
const Label = ({ children }: { children: React.ReactNode }) => <span className="font-mono text-f--2 uppercase tracking-[0.2em] text-white/40">{children}</span>;
const Row = ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={cn("flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.03] px-3.5 py-2.5 text-f--1", className)}>{children}</div>;

export function EvidenceFrame() {
  return (
    <Frame>
      <div className="flex items-center justify-between"><Label>Agent Evidence · Run 8f2a</Label><span className="rounded-full border border-white/15 px-2 py-0.5 font-mono text-f--2 text-white/70">98% confidence</span></div>
      <div className="mt-4 space-y-2">
        <Row><span className="flex items-center gap-2 text-white/85"><MapPin className="h-4 w-4 text-white/50" />Engineering Block B · Floor 2 · Room 204</span><CheckCircle2 className="h-4 w-4 text-white" /></Row>
        <Row><span className="flex items-center gap-2 text-white/85"><Cpu className="h-4 w-4 text-white/50" />Asset AP-204 · Access Point</span><CheckCircle2 className="h-4 w-4 text-white" /></Row>
        <Row><span className="flex items-center gap-2 text-white/85"><Copy className="h-4 w-4 text-white/50" />3 related reports clustered</span><span className="font-mono text-f--2 text-white/50">DUPLICATE</span></Row>
      </div>
      <div className="mt-4 rounded-xl border border-white/10 bg-white/[0.04] p-4">
        <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" /><span className="text-f--1 font-medium">Policy: REQUIRE_HUMAN_APPROVAL</span></div>
        <p className="mt-1.5 text-[13px] leading-relaxed text-white/55">Proposed: dispatch IT technician, notify 42 affected residents. Public communication requires Campus Admin approval.</p>
        <div className="mt-3 flex gap-2"><span className="rounded-full bg-white px-3 py-1.5 text-f--2 font-medium text-black">Approve & Dispatch</span><span className="rounded-full border border-white/20 px-3 py-1.5 text-f--2 text-white/80">Reject</span></div>
      </div>
    </Frame>
  );
}

export function ReportFrame() {
  const steps = ["Ingested", "Triaging", "Policy Check", "Dispatched", "Resolved"];
  return (
    <Frame>
      <Label>Student Report</Label>
      <div className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] p-4 text-f-0 leading-relaxed text-white/90">“Wi-Fi is down in Block B, Room 204. Whole floor can’t connect since 9am.”<span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-pulse bg-white" /></div>
      <div className="mt-5 flex items-center justify-between">
        {steps.map((s, i) => (
          <div key={s} className="flex flex-1 items-center">
            <div className="flex flex-col items-center gap-2">
              <div className={cn("grid h-6 w-6 place-items-center rounded-full border text-f--2 font-mono", i < 4 ? "border-white bg-white text-black" : "border-white/25 text-white/40")}>{i + 1}</div>
              <span className={cn("hidden text-f--2 sm:block", i < 4 ? "text-white/80" : "text-white/35")}>{s}</span>
            </div>
            {i < steps.length - 1 && <div className={cn("mx-1 mb-5 h-px flex-1", i < 3 ? "bg-white/70" : "bg-white/15")} />}
          </div>
        ))}
      </div>
      <div className="mt-5 grid grid-cols-3 gap-2">
        {[["SLA", "2h 00m"], ["Assigned", "IT Ops"], ["Radius", "42 users"]].map(([k, v]) => (
          <div key={k} className="rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-2.5"><Label>{k}</Label><div className="mt-1 text-f--1 font-medium">{v}</div></div>
        ))}
      </div>
    </Frame>
  );
}

export function GraphFrame() {
  const depts = [{ n: "IT & Network", i: Wifi, c: 7 }, { n: "Electrical", i: Zap, c: 3 }, { n: "Plumbing", i: Droplets, c: 2 }, { n: "Safety", i: Flame, c: 1 }];
  return (
    <Frame>
      <div className="flex items-center justify-between"><Label>Operational Graph · Live</Label><Label>13 open</Label></div>
      <div className="relative mt-4 h-52">
        <svg viewBox="0 0 400 200" className="absolute inset-0 h-full w-full">
          {[[200, 100, 60, 40], [200, 100, 340, 40], [200, 100, 60, 160], [200, 100, 340, 160]].map(([x1, y1, x2, y2], i) => (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(255,255,255,0.18)" strokeDasharray="3 5" />
          ))}
          <circle cx="200" cy="100" r="26" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.5)" />
          <text x="200" y="104" textAnchor="middle" fill="#fff" fontSize="10" fontFamily="var(--font-mono)">CAMPUS</text>
        </svg>
        {depts.map((d, i) => (
          <div key={d.n} className={cn("absolute flex items-center gap-2 rounded-full border border-white/12 bg-black/80 px-3 py-1.5 text-f--2", ["left-0 top-2", "right-0 top-2", "left-0 bottom-2", "right-0 bottom-2"][i])}>
            <d.i className="h-3.5 w-3.5 text-white/70" />{d.n}<span className="ml-1 rounded-full bg-white px-1.5 font-mono text-f--2 text-black">{d.c}</span>
          </div>
        ))}
      </div>
      <Row className="mt-2"><span className="text-white/80">Escalated on SLA breach → Campus Admin</span><span className="font-mono text-f--2 text-white/50">AUTO</span></Row>
    </Frame>
  );
}

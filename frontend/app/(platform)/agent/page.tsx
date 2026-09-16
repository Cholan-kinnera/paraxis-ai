"use client";
import Link from "next/link";
import { useIncidents } from "@/lib/hooks";
import { Badge, Card, CardTitle, Empty, PageHeader, Rows } from "@/components/platform/ui";

const stages = [
  ["observe", "Ingest the raw report with correlation headers."],
  ["understand", "Extract category, location, asset, urgency."],
  ["contextualize", "Ground entities in the campus graph."],
  ["detect", "Cluster duplicates via semantic similarity."],
  ["plan", "Propose the next action and priority."],
  ["policy_gate", "ALLOW · DENY · REQUIRE_HUMAN_APPROVAL."],
  ["act", "Execute through typed, registered tools only."],
  ["monitor_resolve", "Track SLA, escalate, verify closure."],
];
const policies = [
  ["OPS_001", "Routine dispatch", "ALLOW", "Standard department task creation and assignment."],
  ["FIN_002", "Spend above threshold", "REQUIRE_HUMAN_APPROVAL", "Any action with estimated cost above the campus limit."],
  ["COM_003", "Public communication", "REQUIRE_HUMAN_APPROVAL", "Broadcasts, mass notifications, and external messages."],
  ["SEC_004", "Cross-tenant access", "DENY", "Any read or write outside the caller's organization or campus."],
  ["SAF_005", "Disciplinary actions", "REQUIRE_HUMAN_APPROVAL", "Anything affecting a student's record or standing."],
];

export default function AgentPage() {
  const inc = useIncidents();
  const candidates = (inc.data ?? []).filter((i) => ["INGESTED", "TRIAGING", "PENDING_APPROVAL"].includes(i.status));
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Intelligence" title="Agent Copilot" sub="A LangGraph workflow that proposes, never decides. Every consequential step is gated by a deterministic policy engine and recorded in the audit log." />
      <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardTitle>Awaiting triage</CardTitle>
          {inc.isLoading ? <Rows n={4} /> : candidates.length === 0 ? <Empty title="Queue is clear" body="New reports will show up here for the copilot to triage." /> : (
            <ul className="divide-y divide-neutral-100">{candidates.map((i) => <li key={i.id}><Link href={`/incidents/${i.id}`} className="group flex items-center gap-4 py-3"><Badge value={i.priority} className="w-24 justify-center" /><div className="min-w-0 flex-1"><div className="truncate text-sm font-medium group-hover:underline">{i.title}</div><div className="truncate text-xs text-neutral-500">{i.description}</div></div><Badge value={i.status} /><span className="hidden text-xs text-neutral-400 sm:block">Run →</span></Link></li>)}</ul>
          )}
        </Card>
        <Card>
          <CardTitle>Workflow graph</CardTitle>
          <ol className="relative ml-2 border-l border-neutral-200">{stages.map(([s, d], i) => <li key={s} className="relative pb-5 pl-6 last:pb-0"><span className="absolute -left-[13px] top-0 grid h-6 w-6 place-items-center rounded-full border border-black bg-white font-mono text-[10px]">{i + 1}</span><div className="font-mono text-xs uppercase tracking-[0.14em]">{s.replace("_", " ")}</div><p className="mt-0.5 text-sm text-neutral-600">{d}</p></li>)}</ol>
        </Card>
      </div>
      <Card>
        <CardTitle>Policy engine · rules</CardTitle>
        <div className="overflow-x-auto"><table className="w-full min-w-[640px] text-sm"><thead><tr className="border-b border-neutral-200 font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500"><th className="py-2 text-left font-normal">Rule</th><th className="py-2 text-left font-normal">Scope</th><th className="py-2 text-left font-normal">Decision</th><th className="py-2 text-left font-normal">Description</th></tr></thead><tbody className="divide-y divide-neutral-100">{policies.map(([id, n, d, desc]) => <tr key={id}><td className="py-3 font-mono text-xs">{id}</td><td className="py-3">{n}</td><td className="py-3"><Badge value={d === "ALLOW" ? "MET" : d === "DENY" ? "CRITICAL" : "PENDING_APPROVAL"} /></td><td className="py-3 text-neutral-600">{desc}</td></tr>)}</tbody></table></div>
      </Card>
    </div>
  );
}

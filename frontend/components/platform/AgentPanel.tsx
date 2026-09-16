"use client";
import { useState } from "react";
import { CheckCircle2, Copy, MapPin, Cpu, ShieldCheck, Sparkles, XCircle } from "lucide-react";
import { useOrchestrate, useResumeRun } from "@/lib/hooks";
import { cn, title } from "@/lib/utils";
import type { AgentRun, Incident } from "@/lib/types";
import { Badge, Button, Card, CardTitle, Drawer } from "./ui";

const STEPS = ["observe", "understand", "contextualize", "detect", "plan", "policy_gate", "act", "monitor_resolve"];

export function AgentPanel({ incident }: { incident: Incident }) {
  const run = useOrchestrate();
  const resume = useResumeRun();
  const [result, setResult] = useState<AgentRun | null>(null);
  const [drawer, setDrawer] = useState(false);
  const r = result;
  const needsApproval = r?.policy?.decision === "REQUIRE_HUMAN_APPROVAL" && r.execution_status === "SUSPENDED";
  const done = new Set(r?.step_history ?? []);

  const decide = (approval_status: "APPROVED" | "REJECTED") =>
    resume.mutate({ thread_id: incident.id, approval_status }, { onSuccess: (d) => { setResult(d); setDrawer(false); } });

  return (
    <Card>
      <CardTitle action={<Button size="sm" variant={r ? "outline" : "primary"} loading={run.isPending} onClick={() => run.mutate(incident, { onSuccess: setResult })}><Sparkles className="h-3.5 w-3.5" />{r ? "Re-run" : "Run copilot"}</Button>}>Agent copilot</CardTitle>
      {run.error && <p className="mb-3 rounded-xl border border-black px-3.5 py-2.5 text-sm">{(run.error as Error).message}</p>}
      {!r && !run.isPending && <p className="text-sm text-neutral-500">Resolve entities, detect duplicates, score priority and propose a governed action. The copilot proposes — you decide.</p>}
      {run.isPending && <div className="space-y-2">{STEPS.map((s, i) => <div key={s} className="flex items-center gap-3 text-sm text-neutral-500"><span className="h-1.5 w-1.5 animate-pulse rounded-full bg-black" style={{ animationDelay: `${i * 120}ms` }} />{title(s)}</div>)}</div>}
      {r && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-1.5">
            {STEPS.map((s, i) => <span key={s} className={cn("rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em]", done.has(s) ? "border-black bg-black text-white" : "border-neutral-200 text-neutral-400")}>{i + 1} {s.replace("_", " ")}</span>)}
          </div>
          <div className="rounded-xl border border-neutral-200 p-4">
            <div className="flex items-center justify-between"><span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">Evidence · {r.agent_run_id}</span><span className="rounded-full border border-neutral-300 px-2 py-0.5 font-mono text-[10px]">{Math.round((r.entities?.confidence ?? 0) * 100)}% confidence</span></div>
            <ul className="mt-3 space-y-2 text-sm">
              <li className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2"><span className="flex items-center gap-2"><MapPin className="h-4 w-4 text-neutral-400" />{[r.entities?.building_name, r.entities?.room_number && `Room ${r.entities.room_number}`].filter(Boolean).join(" · ") || "Location unresolved"}</span>{r.entities?.building_name && <CheckCircle2 className="h-4 w-4" />}</li>
              <li className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2"><span className="flex items-center gap-2"><Cpu className="h-4 w-4 text-neutral-400" />{r.entities?.asset_name ?? "No asset matched"}</span>{r.entities?.asset_name && <CheckCircle2 className="h-4 w-4" />}</li>
              <li className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2"><span className="flex items-center gap-2"><Copy className="h-4 w-4 text-neutral-400" />{r.duplicate?.is_duplicate ? `Duplicate of “${r.duplicate.matched_incident_title}”` : "No duplicates detected"}</span><span className="font-mono text-[10px] text-neutral-500">{Math.round((r.duplicate?.similarity_score ?? 0) * 100)}% sim</span></li>
            </ul>
          </div>
          <div className={cn("rounded-xl border p-4", r.policy?.decision === "DENY" ? "border-black bg-black text-white" : "border-neutral-200")}>
            <div className="flex items-center gap-2 text-sm font-medium"><ShieldCheck className="h-4 w-4" />Policy: {r.policy?.decision.replace(/_/g, " ")}<span className="ml-auto font-mono text-[10px] opacity-60">{r.policy?.rule_id}</span></div>
            <p className={cn("mt-1.5 text-sm", r.policy?.decision === "DENY" ? "text-white/70" : "text-neutral-600")}>{r.policy?.reason}</p>
            {r.proposal && <div className="mt-3 flex flex-wrap items-center gap-2 text-xs"><span className="rounded-full border border-current px-2 py-0.5 font-mono uppercase tracking-wider">{r.proposal.action_type.replace(/_/g, " ")}</span><Badge value={r.proposal.priority} />{r.proposal.estimated_cost > 0 && <span className="font-mono">est. ${r.proposal.estimated_cost}</span>}<span className="opacity-70">{r.proposal.action_justification}</span></div>}
            {needsApproval && <div className="mt-4"><Button size="sm" onClick={() => setDrawer(true)}>Review & decide</Button></div>}
            {r.approval_status && <div className="mt-3 flex items-center gap-2 text-sm">{r.approval_status === "APPROVED" ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}{title(r.approval_status)} by Campus Admin</div>}
          </div>
          <p className="text-sm text-neutral-700">{r.summary}</p>
          <details className="group">
            <summary className="cursor-pointer font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500 hover:text-black">Tool telemetry · {r.executed_tools.length} calls</summary>
            <ul className="mt-3 divide-y divide-neutral-100 rounded-xl border border-neutral-200">{r.executed_tools.map((t) => <li key={t.tool_call_id} className="flex items-center justify-between px-3 py-2 text-xs"><span className="font-mono">{t.tool_name}</span><span className="flex items-center gap-3 text-neutral-500"><span className="font-mono">{t.duration_ms.toFixed(0)}ms</span><Badge value={t.status === "SUCCESS" ? "MET" : "BREACHED"} /></span></li>)}</ul>
          </details>
        </div>
      )}
      <Drawer open={drawer} onClose={() => setDrawer(false)} title="Approval required"
        footer={<div className="flex gap-2"><Button className="flex-1" loading={resume.isPending} onClick={() => decide("APPROVED")}>Approve & Dispatch</Button><Button variant="danger" loading={resume.isPending} onClick={() => decide("REJECTED")}>Reject Action</Button></div>}>
        {r && (
          <div className="space-y-5 text-sm">
            <p className="text-neutral-600">The copilot paused because this action exceeds the autonomous policy envelope. Your decision is recorded in the audit trail.</p>
            <div className="rounded-xl border border-neutral-200 p-4"><div className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">Proposed action</div><div className="mt-1 text-lg font-medium">{r.proposal?.action_type.replace(/_/g, " ")}</div><p className="mt-1 text-neutral-600">{r.proposal?.action_justification}</p></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-neutral-200 p-4"><div className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">Est. cost</div><div className="mt-1 text-lg font-medium">${r.proposal?.estimated_cost ?? 0}</div></div>
              <div className="rounded-xl border border-neutral-200 p-4"><div className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">Priority</div><div className="mt-1"><Badge value={r.proposal?.priority} /></div></div>
            </div>
            <div className="rounded-xl bg-black p-4 text-white"><div className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-white/50">Policy rule</div><div className="mt-1 font-medium">{r.policy?.rule_id}</div><p className="mt-1 text-white/70">{r.policy?.reason}</p>{r.policy?.required_approver_role && <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-white/50">Requires {r.policy.required_approver_role.replace(/_/g, " ")}</p>}</div>
            {resume.error && <p className="rounded-xl border border-black px-3.5 py-2.5">{(resume.error as Error).message}</p>}
          </div>
        )}
      </Drawer>
    </Card>
  );
}

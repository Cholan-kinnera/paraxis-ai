"use client";
import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useDepartments, useTask, useTaskAction, useTaskEvents } from "@/lib/hooks";
import { fmtDate, timeAgo, title } from "@/lib/utils";
import { Badge, Button, Card, CardTitle, ErrorBox, Field, KV, Select, Skeleton, Textarea, Timeline } from "@/components/platform/ui";

const dur = (ms: number) => { const m = Math.ceil(ms / 6e4); return m >= 60 ? `${Math.floor(m / 60)}h ${m % 60}m` : `${m}m`; };

function SlaMeter({ label, start, due, done, breached }: { label: string; start: string; due?: string | null; done?: string | null; breached?: string | null }) {
  if (!due) return null;
  const s = +new Date(start), d = +new Date(due), now = done ? +new Date(done) : Date.now();
  const pct = Math.min(100, Math.max(0, ((now - s) / (d - s)) * 100));
  const left = d - Date.now();
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-xs"><span className="font-mono uppercase tracking-[0.16em] text-neutral-500">{label}</span><span className={breached ? "font-medium" : "text-neutral-500"}>{done ? `met ${timeAgo(done)}` : breached ? `breached ${timeAgo(breached)}` : left > 0 ? `${dur(left)} left` : "overdue"}</span></div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-100"><div className={`h-full rounded-full ${breached ? "bg-black" : done ? "bg-neutral-400" : "bg-black"}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>();
  const q = useTask(id);
  const events = useTaskEvents(id);
  const depts = useDepartments();
  const act = useTaskAction(id);
  const [notes, setNotes] = useState("");
  const [dept, setDept] = useState("");
  const t = q.data;
  if (q.error) return <ErrorBox error={q.error} retry={() => q.refetch()} />;
  if (!t) return <div className="space-y-4"><Skeleton className="h-8 w-40" /><Skeleton className="h-12 w-2/3" /><Skeleton className="h-64" /></div>;
  const s = t.sla_tracking;
  const can = { assign: ["PENDING", "ASSIGNED"].includes(t.status), start: t.status === "ASSIGNED" || t.status === "BLOCKED", complete: t.status === "IN_PROGRESS", cancel: !["COMPLETED", "CANCELLED"].includes(t.status) };

  return (
    <div className="space-y-6">
      <Link href="/tasks" className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500 hover:text-black"><ArrowLeft className="h-3.5 w-3.5" />Tasks</Link>
      <div className="flex flex-col gap-4 border-b border-neutral-200 pb-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2"><Badge value={t.priority} /><Badge value={t.status} />{s && <Badge value={s.state} />}<span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-400">{title(t.task_type)} · {t.id.slice(0, 8)}</span></div>
          <h1 className="mt-3 text-3xl font-medium tracking-tightest sm:text-4xl">{t.title}</h1>
          {t.description && <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-neutral-700">{t.description}</p>}
          {t.incident && <p className="mt-3 text-xs text-neutral-500">For incident <Link href={`/incidents/${t.incident}`} className="underline">{t.incident_title}</Link></p>}
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {can.start && <Button size="sm" loading={act.isPending} onClick={() => act.mutate({ action: "start" })}>Start work</Button>}
          {can.complete && <Button size="sm" loading={act.isPending} onClick={() => act.mutate({ action: "complete", body: { notes } })}>Complete</Button>}
          {can.cancel && <Button size="sm" variant="danger" loading={act.isPending} onClick={() => act.mutate({ action: "cancel", body: { reason: notes || "Cancelled from console" } })}>Cancel</Button>}
        </div>
      </div>
      {act.error && <ErrorBox error={act.error} />}
      <div className="grid gap-4 xl:grid-cols-2 [&>*]:min-w-0">
        <div className="space-y-4">
          <Card>
            <CardTitle>SLA · {s?.sla_name ?? "not tracked"}</CardTitle>
            {s ? <div className="space-y-5"><SlaMeter label="Response" start={s.started_at} due={s.response_due_at} done={s.response_completed_at} breached={s.response_breached_at} /><SlaMeter label="Resolution" start={s.started_at} due={s.resolution_due_at} done={s.resolution_completed_at} breached={s.resolution_breached_at} /></div> : <p className="text-sm text-neutral-500">No SLA attached to this task.</p>}
          </Card>
          <Card>
            <CardTitle>Details</CardTitle>
            <KV items={[["Assignee", t.assigned_user_name], ["Department", t.assigned_department_name], ["Due", t.due_at ? fmtDate(t.due_at) : null], ["Started", t.started_at ? fmtDate(t.started_at) : null], ["Completed", t.completed_at ? fmtDate(t.completed_at) : null], ["Created", fmtDate(t.created_at)]]} />
          </Card>
          <Card className="space-y-4">
            <CardTitle>Actions</CardTitle>
            {can.assign && <div className="flex items-end gap-2"><div className="flex-1"><Field label="Assign department"><Select value={dept} onChange={(e) => setDept(e.target.value)}><option value="">Select…</option>{depts.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select></Field></div><Button variant="outline" disabled={!dept} loading={act.isPending} onClick={() => act.mutate({ action: "assign", body: { assigned_department: dept } })}>Assign</Button></div>}
            <Field label="Notes / reason" hint="Included with complete or cancel."><Textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="min-h-[80px]" /></Field>
          </Card>
        </div>
        <Card>
          <CardTitle>Timeline</CardTitle>
          {events.isLoading ? <Skeleton className="h-40" /> : <Timeline items={(events.data ?? []).map((e) => ({ id: e.id, label: title(e.event_type), body: e.message, when: timeAgo(e.created_at), actor: e.actor_email ?? e.actor_type, meta: e.from_status && e.to_status ? `${e.from_status} → ${e.to_status}` : undefined }))} />}
        </Card>
      </div>
    </div>
  );
}

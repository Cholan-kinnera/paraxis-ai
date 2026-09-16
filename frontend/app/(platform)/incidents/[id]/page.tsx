"use client";
import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useDepartments, useIncident, useIncidentEvents, useTasks, useUpdateIncident } from "@/lib/hooks";
import { fmtDate, timeAgo, title } from "@/lib/utils";
import type { IncidentStatus } from "@/lib/types";
import { Badge, Button, Card, CardTitle, ErrorBox, Field, KV, Select, Skeleton, Textarea, Timeline } from "@/components/platform/ui";
import { AgentPanel } from "@/components/platform/AgentPanel";

const NEXT: Record<string, IncidentStatus[]> = {
  INGESTED: ["TRIAGING", "ASSIGNED", "PENDING_APPROVAL", "IN_PROGRESS", "DUPLICATE_LINKED", "REJECTED"],
  TRIAGING: ["ASSIGNED", "PENDING_APPROVAL", "IN_PROGRESS", "DUPLICATE_LINKED", "REJECTED"],
  PENDING_APPROVAL: ["ASSIGNED", "REJECTED"],
  ASSIGNED: ["IN_PROGRESS", "ESCALATED", "RESOLVED", "REJECTED"],
  IN_PROGRESS: ["RESOLVED", "ESCALATED", "ASSIGNED", "REJECTED"],
  ESCALATED: ["IN_PROGRESS", "ASSIGNED", "RESOLVED"],
  RESOLVED: ["VERIFIED", "REOPENED", "CLOSED"],
  VERIFIED: ["CLOSED", "REOPENED"],
  REOPENED: ["ASSIGNED", "IN_PROGRESS", "ESCALATED"],
  REJECTED: ["CLOSED", "REOPENED"],
  DUPLICATE_LINKED: ["CLOSED", "INGESTED"],
  CLOSED: [],
};
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const inc = useIncident(id);
  const events = useIncidentEvents(id);
  const tasks = useTasks({ incident: id });
  const depts = useDepartments();
  const update = useUpdateIncident(id);
  const [notes, setNotes] = useState("");
  const i = inc.data;

  if (inc.error) return <ErrorBox error={inc.error} retry={() => inc.refetch()} />;
  if (!i) return <div className="space-y-4"><Skeleton className="h-8 w-40" /><Skeleton className="h-12 w-2/3" /><Skeleton className="h-64" /></div>;
  const next = NEXT[i.status] ?? [];
  const move = (status: IncidentStatus) => update.mutate({ status, ...(["RESOLVED", "CLOSED", "VERIFIED"].includes(status) && notes ? { resolution_notes: notes } : {}) });
  const linkedTasks = (tasks.data ?? []).filter((t) => t.incident === id);

  return (
    <div className="space-y-6">
      <Link href="/incidents" className="inline-flex items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500 hover:text-black"><ArrowLeft className="h-3.5 w-3.5" />Incidents</Link>
      <div className="flex flex-col gap-4 border-b border-neutral-200 pb-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2"><Badge value={i.priority} /><Badge value={i.status} /><span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-400">{title(i.category)} · {i.source} · {i.id.slice(0, 8)}</span></div>
          <h1 className="mt-3 text-3xl font-medium tracking-tightest sm:text-4xl">{i.title}</h1>
          <p className="mt-3 max-w-3xl text-[15px] leading-relaxed text-neutral-700">{i.description}</p>
          <p className="mt-3 text-xs text-neutral-500">Reported by {i.reporter_name ?? "—"} · {fmtDate(i.created_at)} · updated {timeAgo(i.updated_at)}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2 lg:max-w-xs lg:justify-end">
          {next.map((s) => <Button key={s} size="sm" variant={["RESOLVED", "VERIFIED", "CLOSED", "IN_PROGRESS", "ASSIGNED"].includes(s) ? "primary" : "outline"} loading={update.isPending} onClick={() => move(s)}>{title(s)}</Button>)}
        </div>
      </div>
      {update.error && <ErrorBox error={update.error} />}

      <div className="grid gap-4 xl:grid-cols-[1fr_1.1fr] [&>*]:min-w-0">
        <div className="space-y-4">
          <Card>
            <CardTitle>Context</CardTitle>
            <KV items={[
              ["Building", i.building_name ? `${i.building_name} (${i.building_code})` : null],
              ["Floor", i.floor_label],
              ["Room", i.room_number],
              ["Asset", i.asset_tag ? `${i.asset_tag} · ${i.asset_name}` : null],
              ["Department", i.department_name],
              ["Assigned to", i.assigned_to_name],
              ["Duplicate of", i.is_duplicate_of_id ? <Link className="underline" href={`/incidents/${i.is_duplicate_of_id}`}>{i.is_duplicate_of_id.slice(0, 8)}</Link> : null],
              ["Resolved", i.resolved_at ? fmtDate(i.resolved_at) : null],
              ["Resolution notes", i.resolution_notes],
            ]} />
          </Card>
          <Card className="space-y-4">
            <CardTitle>Triage</CardTitle>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Priority"><Select value={i.priority} onChange={(e) => update.mutate({ priority: e.target.value as never })}>{PRIORITIES.map((p) => <option key={p} value={p}>{title(p)}</option>)}</Select></Field>
              <Field label="Department"><Select value={i.department_id ?? ""} onChange={(e) => update.mutate({ department_id: e.target.value || null })}><option value="">Unrouted</option>{depts.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select></Field>
            </div>
            <Field label="Resolution notes" hint="Attached when you mark the incident resolved, verified or closed."><Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What was done, and how it was verified." className="min-h-[90px]" /></Field>
          </Card>
          <Card>
            <CardTitle action={<Button size="sm" variant="outline" href={`/tasks?incident=${id}`}>Open tasks</Button>}>Dispatched work</CardTitle>
            {linkedTasks.length === 0 ? <p className="text-sm text-neutral-500">No tasks dispatched yet.</p> : (
              <ul className="space-y-2">{linkedTasks.map((t) => <li key={t.id}><Link href={`/tasks/${t.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-neutral-200 px-3 py-2.5 hover:border-black"><div className="min-w-0"><div className="truncate text-sm">{t.title}</div><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-500">{title(t.task_type)} · {t.assigned_user_name ?? t.assigned_department_name ?? "Unassigned"}</div></div><div className="flex items-center gap-2"><Badge value={t.sla_tracking?.state} /><Badge value={t.status} /></div></Link></li>)}</ul>
            )}
          </Card>
        </div>
        <div className="space-y-4">
          <AgentPanel incident={i} />
          <Card>
            <CardTitle>Timeline</CardTitle>
            {events.isLoading ? <Skeleton className="h-40" /> : <Timeline items={(events.data ?? []).map((e) => ({ id: e.id, label: title(e.event_type), body: e.description, when: timeAgo(e.created_at), actor: e.actor_type, meta: e.request_id }))} />}
          </Card>
        </div>
      </div>
    </div>
  );
}

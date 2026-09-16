"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCreateTask, useDepartments, useIncidents, useTasks } from "@/lib/hooks";
import { fmtDate, timeAgo, title } from "@/lib/utils";
import { Badge, Button, Drawer, Empty, ErrorBox, Field, Input, PageHeader, Rows, Select, Table, Td, Textarea } from "@/components/platform/ui";

const STATUSES = ["PENDING", "ASSIGNED", "IN_PROGRESS", "BLOCKED", "COMPLETED", "CANCELLED"];
const TYPES = ["INSPECTION", "REPAIR", "MAINTENANCE", "COMMUNICATION", "ESCALATION", "FOLLOW_UP", "OTHER"];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

function SlaCell({ t }: { t: { sla_tracking?: { state: string; resolution_due_at?: string | null } | null } }) {
  const s = t.sla_tracking;
  if (!s) return <span className="text-neutral-400">—</span>;
  const due = s.resolution_due_at ? new Date(s.resolution_due_at).getTime() - Date.now() : null;
  const h = due != null ? Math.round(due / 36e5) : null;
  return <div className="flex items-center gap-2"><Badge value={s.state} />{h != null && <span className="font-mono text-[10.5px] text-neutral-500">{h >= 0 ? `${h}h left` : `${-h}h over`}</span>}</div>;
}

function NewTask({ open, onClose, incidentId }: { open: boolean; onClose: () => void; incidentId?: string }) {
  const create = useCreateTask();
  const incidents = useIncidents();
  const depts = useDepartments();
  const [f, setF] = useState({ incident: incidentId ?? "", title: "", description: "", task_type: "REPAIR", priority: "", assigned_department: "" });
  const up = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setF((s) => ({ ...s, [k]: e.target.value }));
  const submit = () => create.mutate(Object.fromEntries(Object.entries(f).filter(([, v]) => v)) as never, { onSuccess: onClose });
  return (
    <Drawer open={open} onClose={onClose} title="Dispatch a task" footer={<div className="flex gap-2"><Button className="flex-1" loading={create.isPending} onClick={submit} disabled={!f.title || !f.incident}>Create task</Button><Button variant="outline" onClick={onClose}>Cancel</Button></div>}>
      <div className="space-y-4">
        <Field label="Incident"><Select value={f.incident} onChange={up("incident")}><option value="">Select incident…</option>{incidents.data?.map((i) => <option key={i.id} value={i.id}>{i.title}</option>)}</Select></Field>
        <Field label="Title"><Input value={f.title} onChange={up("title")} placeholder="e.g. Inspect AP-204 PoE & radio status" /></Field>
        <Field label="Description"><Textarea value={f.description} onChange={up("description")} className="min-h-[100px]" /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type"><Select value={f.task_type} onChange={up("task_type")}>{TYPES.map((t) => <option key={t} value={t}>{title(t)}</option>)}</Select></Field>
          <Field label="Priority" hint="Defaults to the incident's."><Select value={f.priority} onChange={up("priority")}><option value="">Inherit</option>{PRIORITIES.map((t) => <option key={t} value={t}>{title(t)}</option>)}</Select></Field>
        </div>
        <Field label="Department"><Select value={f.assigned_department} onChange={up("assigned_department")}><option value="">Unassigned</option>{depts.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select></Field>
        {create.error && <p className="rounded-xl border border-black px-3.5 py-2.5 text-sm">{(create.error as Error).message}</p>}
      </div>
    </Drawer>
  );
}

function TasksList() {
  const sp = useSearchParams();
  const router = useRouter();
  const filters = { status: sp.get("status") ?? undefined, task_type: sp.get("task_type") ?? undefined, incident: sp.get("incident") ?? undefined };
  const { data, isLoading, error, refetch } = useTasks(filters);
  const [open, setOpen] = useState(false);
  const set = (k: string, v: string) => { const p = new URLSearchParams(sp.toString()); v ? p.set(k, v) : p.delete(k); router.replace(`/tasks?${p.toString()}`); };
  const rows = data ?? [];
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Dispatch" title="Tasks & SLAs" sub="Operational work orders with live response and resolution timers. Breaches escalate automatically." actions={<Button onClick={() => setOpen(true)}>Dispatch task</Button>} />
      <div className="flex flex-wrap gap-2">
        <Select value={filters.status ?? ""} onChange={(e) => set("status", e.target.value)} className="w-auto"><option value="">All statuses</option>{STATUSES.map((s) => <option key={s} value={s}>{title(s)}</option>)}</Select>
        <Select value={filters.task_type ?? ""} onChange={(e) => set("task_type", e.target.value)} className="w-auto"><option value="">All types</option>{TYPES.map((s) => <option key={s} value={s}>{title(s)}</option>)}</Select>
        {filters.incident && <Button size="sm" variant="outline" onClick={() => set("incident", "")}>Clear incident filter ×</Button>}
        <span className="ml-auto self-center font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">{rows.length} tasks</span>
      </div>
      {error && <ErrorBox error={error} retry={() => refetch()} />}
      {isLoading ? <Rows n={6} /> : rows.length === 0 ? <Empty title="No tasks" body="Dispatch work from an incident, or create a task directly." action={<Button size="sm" onClick={() => setOpen(true)}>Dispatch task</Button>} /> : (
        <Table head={["Priority", "Task", "Incident", "Assignee", "SLA", "Status", "Due"]}>
          {rows.map((t) => (
            <tr key={t.id} className="group cursor-pointer transition-colors hover:bg-neutral-50" onClick={() => router.push(`/tasks/${t.id}`)}>
              <Td><Badge value={t.priority} /></Td>
              <Td><Link href={`/tasks/${t.id}`} className="font-medium group-hover:underline">{t.title}</Link><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-500">{title(t.task_type)}</div></Td>
              <Td className="max-w-[220px] truncate text-xs text-neutral-600">{t.incident_title ?? "—"}</Td>
              <Td className="text-xs text-neutral-600">{t.assigned_user_name ?? t.assigned_department_name ?? "Unassigned"}</Td>
              <Td><SlaCell t={t} /></Td>
              <Td><Badge value={t.status} /></Td>
              <Td className="font-mono text-xs text-neutral-400">{t.due_at ? fmtDate(t.due_at) : timeAgo(t.updated_at)}</Td>
            </tr>
          ))}
        </Table>
      )}
      <NewTask open={open} onClose={() => setOpen(false)} incidentId={filters.incident} />
    </div>
  );
}
export default function Page() { return <Suspense><TasksList /></Suspense>; }

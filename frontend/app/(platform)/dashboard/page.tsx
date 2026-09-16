"use client";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { useIncidents, useTasks, useProfile } from "@/lib/hooks";
import { timeAgo, title } from "@/lib/utils";
import { Badge, Button, Card, CardTitle, Empty, ErrorBox, PageHeader, Rows, Stat } from "@/components/platform/ui";
import type { Incident, Task } from "@/lib/types";

const OPEN = new Set(["INGESTED", "TRIAGING", "PENDING_APPROVAL", "ASSIGNED", "IN_PROGRESS", "ESCALATED", "REOPENED"]);

function Bars({ data }: { data: [string, number][] }) {
  const max = Math.max(1, ...data.map((d) => d[1]));
  return (
    <div className="space-y-3">
      {data.map(([k, v]) => (
        <div key={k}>
          <div className="mb-1 flex justify-between text-xs"><span className="text-neutral-700">{title(k)}</span><span className="font-mono text-neutral-500">{v}</span></div>
          <div className="h-1.5 w-full rounded-full bg-neutral-100"><div className="h-full rounded-full bg-black transition-all duration-700" style={{ width: `${(v / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const me = useProfile();
  const inc = useIncidents();
  const tasks = useTasks();
  const incidents = inc.data ?? [];
  const open = incidents.filter((i) => OPEN.has(i.status));
  const critical = open.filter((i) => i.priority === "CRITICAL" || i.priority === "HIGH");
  const approval = open.filter((i) => i.status === "PENDING_APPROVAL");
  const atRisk = (tasks.data ?? []).filter((t) => t.sla_tracking && ["AT_RISK", "BREACHED"].includes(t.sla_tracking.state));
  const byCat = Object.entries(incidents.reduce<Record<string, number>>((a, i) => ((a[i.category] = (a[i.category] ?? 0) + 1), a), {})).sort((a, b) => b[1] - a[1]) as [string, number][];
  const recent = [...incidents].sort((a, b) => +new Date(b.updated_at) - +new Date(a.updated_at)).slice(0, 8);
  const activeTasks = (tasks.data ?? []).filter((t) => ["ASSIGNED", "IN_PROGRESS", "BLOCKED", "PENDING"].includes(t.status)).slice(0, 6);
  const hour = new Date().getHours();

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={me.data?.primary_campus?.name ?? "Command Center"}
        title={<>{hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening"}{me.data ? `, ${me.data.full_name.split(" ")[0]}.` : "."}</>}
        sub="Live operational picture across every department. Nothing here moved without a policy check."
        actions={<Button href="/incidents/new">Report Incident</Button>}
      />
      {inc.error && <ErrorBox error={inc.error} retry={() => inc.refetch()} />}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Open incidents" value={inc.isLoading ? "…" : open.length} delta={`${incidents.length} total`} href="/incidents" />
        <Stat label="High & critical" value={inc.isLoading ? "…" : critical.length} delta="needs attention" href="/incidents?priority=CRITICAL" />
        <Stat label="Pending approval" value={inc.isLoading ? "…" : approval.length} delta="human-in-the-loop" href="/incidents?status=PENDING_APPROVAL" />
        <Stat label="SLA at risk" value={tasks.isLoading ? "…" : atRisk.length} delta={`${tasks.data?.length ?? 0} tasks tracked`} href="/tasks" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr] [&>*]:min-w-0">
        <Card>
          <CardTitle action={<Link href="/incidents" className="flex items-center gap-1 text-xs text-neutral-500 hover:text-black">View all <ArrowUpRight className="h-3 w-3" /></Link>}>Live incident feed</CardTitle>
          {inc.isLoading ? <Rows /> : recent.length === 0 ? <Empty title="No incidents yet" body="Reports will appear here the moment they are ingested." action={<Button href="/incidents/new" size="sm">Report one</Button>} /> : (
            <ul className="divide-y divide-neutral-100">
              {recent.map((i: Incident) => (
                <li key={i.id}>
                  <Link href={`/incidents/${i.id}`} className="group flex items-center gap-4 py-3">
                    <Badge value={i.priority} className="w-24 justify-center" />
                    <div className="min-w-0 flex-1"><div className="truncate text-sm font-medium group-hover:underline">{i.title}</div><div className="truncate font-mono text-[10.5px] uppercase tracking-[0.14em] text-neutral-500">{[i.building_code, i.room_number && `Room ${i.room_number}`, i.department_name].filter(Boolean).join(" · ") || title(i.category)}</div></div>
                    <Badge value={i.status} />
                    <span className="hidden w-16 text-right font-mono text-[10.5px] text-neutral-400 sm:block">{timeAgo(i.updated_at)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <div className="space-y-4">
          <Card><CardTitle>Pattern insights</CardTitle>{inc.isLoading ? <Rows n={4} /> : byCat.length ? <Bars data={byCat} /> : <p className="text-sm text-neutral-500">No data yet.</p>}</Card>
          <Card>
            <CardTitle action={<Link href="/tasks" className="flex items-center gap-1 text-xs text-neutral-500 hover:text-black">All tasks <ArrowUpRight className="h-3 w-3" /></Link>}>Active dispatch</CardTitle>
            {tasks.isLoading ? <Rows n={3} /> : activeTasks.length === 0 ? <p className="text-sm text-neutral-500">No active tasks.</p> : (
              <ul className="space-y-2">
                {activeTasks.map((t: Task) => (
                  <li key={t.id}><Link href={`/tasks/${t.id}`} className="flex items-center justify-between gap-3 rounded-xl border border-neutral-200 px-3 py-2.5 transition-colors hover:border-black"><div className="min-w-0"><div className="truncate text-sm">{t.title}</div><div className="truncate font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-500">{t.assigned_user_name ?? t.assigned_department_name ?? "Unassigned"}</div></div><Badge value={t.sla_tracking?.state ?? t.status} /></Link></li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

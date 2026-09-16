"use client";
import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useIncidents } from "@/lib/hooks";
import { timeAgo, title } from "@/lib/utils";
import { Badge, Button, Empty, ErrorBox, Input, PageHeader, Rows, Select, Table, Td } from "@/components/platform/ui";

const STATUSES = ["INGESTED", "TRIAGING", "PENDING_APPROVAL", "ASSIGNED", "IN_PROGRESS", "ESCALATED", "RESOLVED", "VERIFIED", "CLOSED", "REOPENED", "REJECTED", "DUPLICATE_LINKED"];
const PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const CATEGORIES = ["IT_NETWORK", "ELECTRICAL", "PLUMBING", "HVAC", "SAFETY", "FACILITY", "OTHER"];

function IncidentsList() {
  const sp = useSearchParams();
  const router = useRouter();
  const filters = { status: sp.get("status") ?? undefined, priority: sp.get("priority") ?? undefined, category: sp.get("category") ?? undefined };
  const [q, setQ] = useState("");
  const { data, isLoading, error, refetch } = useIncidents(filters);
  const rows = useMemo(() => (data ?? []).filter((i) => !q || `${i.title} ${i.description} ${i.building_name} ${i.room_number}`.toLowerCase().includes(q.toLowerCase())), [data, q]);
  const set = (k: string, v: string) => { const p = new URLSearchParams(sp.toString()); v ? p.set(k, v) : p.delete(k); router.replace(`/incidents?${p.toString()}`); };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Operations" title="Incidents" sub="Every report, grounded in the campus graph and tracked to verified resolution." actions={<Button href="/incidents/new">Report Incident</Button>} />
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Search title, description, location…" value={q} onChange={(e) => setQ(e.target.value)} className="w-full sm:w-72" />
        <Select value={filters.status ?? ""} onChange={(e) => set("status", e.target.value)} className="w-auto"><option value="">All statuses</option>{STATUSES.map((s) => <option key={s} value={s}>{title(s)}</option>)}</Select>
        <Select value={filters.priority ?? ""} onChange={(e) => set("priority", e.target.value)} className="w-auto"><option value="">All priorities</option>{PRIORITIES.map((s) => <option key={s} value={s}>{title(s)}</option>)}</Select>
        <Select value={filters.category ?? ""} onChange={(e) => set("category", e.target.value)} className="w-auto"><option value="">All categories</option>{CATEGORIES.map((s) => <option key={s} value={s}>{title(s)}</option>)}</Select>
        <span className="ml-auto self-center font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500">{rows.length} results</span>
      </div>
      {error && <ErrorBox error={error} retry={() => refetch()} />}
      {isLoading ? <Rows n={8} /> : rows.length === 0 ? <Empty title="No incidents match" body="Try clearing filters or report a new incident." action={<Button href="/incidents/new" size="sm">Report Incident</Button>} /> : (
        <Table head={["Priority", "Incident", "Location", "Category", "Assigned", "Status", "Updated"]}>
          {rows.map((i) => (
            <tr key={i.id} className="group cursor-pointer transition-colors hover:bg-neutral-50" onClick={() => router.push(`/incidents/${i.id}`)}>
              <Td><Badge value={i.priority} /></Td>
              <Td><Link href={`/incidents/${i.id}`} className="font-medium group-hover:underline">{i.title}</Link><div className="mt-0.5 max-w-md truncate text-xs text-neutral-500">{i.description}</div></Td>
              <Td className="font-mono text-xs text-neutral-600">{[i.building_code, i.floor_label, i.room_number && `R-${i.room_number}`].filter(Boolean).join(" / ") || "—"}</Td>
              <Td className="text-xs text-neutral-600">{title(i.category)}</Td>
              <Td className="text-xs text-neutral-600">{i.assigned_to_name ?? i.department_name ?? "—"}</Td>
              <Td><Badge value={i.status} /></Td>
              <Td className="font-mono text-xs text-neutral-400">{timeAgo(i.updated_at)}</Td>
            </tr>
          ))}
        </Table>
      )}
    </div>
  );
}

export default function Page() { return <Suspense><IncidentsList /></Suspense>; }

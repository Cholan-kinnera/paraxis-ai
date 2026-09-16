"use client";
import { useState } from "react";
import { useAssets, useBuildings, useDepartments, useFloors, useIncidents, useRooms } from "@/lib/hooks";
import { cn, title } from "@/lib/utils";
import { Badge, Card, CardTitle, Empty, ErrorBox, PageHeader, Rows, Stat } from "@/components/platform/ui";

const OPEN = new Set(["INGESTED", "TRIAGING", "PENDING_APPROVAL", "ASSIGNED", "IN_PROGRESS", "ESCALATED", "REOPENED"]);

export default function CampusPage() {
  const b = useBuildings(); const d = useDepartments(); const inc = useIncidents();
  const [sel, setSel] = useState<string | null>(null);
  const floors = useFloors(sel ?? undefined);
  const rooms = useRooms(sel ? { building_id: sel } : undefined);
  const assets = useAssets(sel ? { building_id: sel } : undefined);
  const openByBuilding = (inc.data ?? []).filter((i) => OPEN.has(i.status)).reduce<Record<string, number>>((a, i) => (i.building_id ? ((a[i.building_id] = (a[i.building_id] ?? 0) + 1), a) : a), {});
  const selB = b.data?.find((x) => x.id === sel);

  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Operational graph" title="Campus" sub="The canonical physical hierarchy every report is grounded in: buildings, floors, rooms, and assets." />
      {b.error && <ErrorBox error={b.error} retry={() => b.refetch()} />}
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Buildings" value={b.data?.length ?? "…"} />
        <Stat label="Departments" value={d.data?.length ?? "…"} />
        <Stat label="Open incidents on graph" value={Object.values(openByBuilding).reduce((a, n) => a + n, 0)} />
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr] [&>*]:min-w-0">
        <Card pad={false}>
          <div className="border-b border-neutral-200 px-5 py-4"><CardTitle>Buildings</CardTitle></div>
          {b.isLoading ? <div className="p-5"><Rows n={4} /></div> : !b.data?.length ? <div className="p-5"><Empty title="No buildings" body="Seed the campus graph to see it here." /></div> : (
            <ul className="divide-y divide-neutral-100">
              {b.data.map((x) => (
                <li key={x.id}>
                  <button onClick={() => setSel(x.id === sel ? null : x.id)} className={cn("flex w-full items-center gap-4 px-5 py-3.5 text-left transition-colors hover:bg-neutral-50", sel === x.id && "bg-black text-white hover:bg-black")}>
                    <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-lg border font-mono text-[10px]", sel === x.id ? "border-white/30" : "border-neutral-300")}>{x.code.slice(0, 3)}</span>
                    <span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{x.name}</span><span className={cn("block font-mono text-[10px] uppercase tracking-[0.14em]", sel === x.id ? "text-white/60" : "text-neutral-500")}>{x.floors_count ?? "—"} floors · {x.status ?? "active"}</span></span>
                    {openByBuilding[x.id] ? <span className={cn("rounded-full px-2 py-0.5 font-mono text-[10px]", sel === x.id ? "bg-white text-black" : "bg-black text-white")}>{openByBuilding[x.id]} open</span> : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <div className="space-y-4">
          {!sel ? (
            <Card><CardTitle>Departments</CardTitle><ul className="grid gap-2 sm:grid-cols-2">{(d.data ?? []).map((x) => <li key={x.id} className="rounded-xl border border-neutral-200 px-3.5 py-3"><div className="text-sm font-medium">{x.name}</div><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-500">{x.code ?? "—"}</div></li>)}</ul>{!d.data?.length && !d.isLoading && <p className="text-sm text-neutral-500">No departments.</p>}</Card>
          ) : (
            <>
              <Card>
                <CardTitle>{selB?.name} · Floors</CardTitle>
                {floors.isLoading ? <Rows n={2} /> : <div className="flex flex-wrap gap-2">{(floors.data ?? []).map((f) => <span key={f.id} className="rounded-full border border-neutral-300 px-3 py-1.5 text-xs">{f.label}</span>)}{!floors.data?.length && <p className="text-sm text-neutral-500">No floors.</p>}</div>}
              </Card>
              <Card>
                <CardTitle>Rooms</CardTitle>
                {rooms.isLoading ? <Rows n={3} /> : !rooms.data?.length ? <p className="text-sm text-neutral-500">No rooms.</p> : <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{rooms.data.map((r) => <li key={r.id} className="rounded-xl border border-neutral-200 px-3.5 py-3"><div className="flex items-center justify-between"><span className="font-mono text-sm">{r.room_number}</span><Badge value={r.status === "ACTIVE" ? undefined : r.status} /></div><div className="truncate text-xs text-neutral-600">{r.name ?? title(r.room_type)}</div><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-400">{r.floor_label}{r.capacity ? ` · cap ${r.capacity}` : ""}</div></li>)}</ul>}
              </Card>
              <Card>
                <CardTitle>Assets</CardTitle>
                {assets.isLoading ? <Rows n={3} /> : !assets.data?.length ? <p className="text-sm text-neutral-500">No assets.</p> : <ul className="divide-y divide-neutral-100">{assets.data.map((a) => <li key={a.id} className="flex items-center justify-between gap-3 py-2.5 text-sm"><div className="min-w-0"><span className="font-mono text-xs text-neutral-500">{a.asset_tag}</span><span className="ml-2">{a.name}</span></div><div className="flex items-center gap-3 text-xs text-neutral-500"><span>{a.room_number ? `R-${a.room_number}` : ""}</span><Badge value={a.status} /></div></li>)}</ul>}
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useBuildings, useCreateIncident, useDepartments, useFloors, useRooms, useAssets } from "@/lib/hooks";
import { title } from "@/lib/utils";
import { Button, Card, CardTitle, Field, Input, PageHeader, Select, Textarea } from "@/components/platform/ui";

const CATEGORIES = ["IT_NETWORK", "ELECTRICAL", "PLUMBING", "HVAC", "SAFETY", "FACILITY", "OTHER"];
const PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const examples = ["Wi-Fi is down in Block B, Room 204. Whole floor can't connect since 9am.", "Corridor light near the server room is flickering badly.", "AC in Lecture Hall 3 blowing warm air during exams."];

export default function NewIncident() {
  const router = useRouter();
  const create = useCreateIncident();
  const [f, setF] = useState({ title: "", description: "", category: "IT_NETWORK", priority: "MEDIUM", building_id: "", floor_id: "", room_id: "", asset_id: "", department_id: "" });
  const up = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setF((s) => ({ ...s, [k]: e.target.value }));
  const buildings = useBuildings(); const floors = useFloors(f.building_id || undefined); const rooms = useRooms(f.floor_id ? { floor_id: f.floor_id } : f.building_id ? { building_id: f.building_id } : undefined); const assets = useAssets(f.room_id ? { room_id: f.room_id } : undefined); const depts = useDepartments();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const body = Object.fromEntries(Object.entries(f).filter(([, v]) => v !== ""));
    create.mutate(body, { onSuccess: (i) => router.push(`/incidents/${i.id}`) });
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Ingest" title="Report an incident" sub="Describe what's happening in plain language. Location context makes triage faster, but it's optional — the copilot can resolve it." />
      <form onSubmit={submit} className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card className="space-y-5">
          <CardTitle>What happened?</CardTitle>
          <Field label="Title"><Input required maxLength={200} value={f.title} onChange={up("title")} placeholder="Short summary, e.g. Wi-Fi down in Block B Room 204" /></Field>
          <Field label="Description"><Textarea required value={f.description} onChange={up("description")} placeholder="Tell us what you're seeing, since when, and how many people are affected." className="min-h-[180px]" /></Field>
          <div className="flex flex-wrap gap-2">{examples.map((x) => <button type="button" key={x} onClick={() => setF((s) => ({ ...s, description: x, title: s.title || x.split(".")[0] }))} className="rounded-full border border-neutral-300 px-3 py-1.5 text-left text-xs text-neutral-600 transition-colors hover:border-black hover:text-black">“{x.slice(0, 44)}…”</button>)}</div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Category"><Select value={f.category} onChange={up("category")}>{CATEGORIES.map((c) => <option key={c} value={c}>{title(c)}</option>)}</Select></Field>
            <Field label="Priority" hint="Agents may re-score this from affected radius."><Select value={f.priority} onChange={up("priority")}>{PRIORITIES.map((c) => <option key={c} value={c}>{title(c)}</option>)}</Select></Field>
          </div>
        </Card>
        <div className="space-y-4">
          <Card className="space-y-4">
            <CardTitle>Location context</CardTitle>
            <Field label="Building"><Select value={f.building_id} onChange={(e) => setF((s) => ({ ...s, building_id: e.target.value, floor_id: "", room_id: "", asset_id: "" }))}><option value="">Unknown</option>{buildings.data?.map((b) => <option key={b.id} value={b.id}>{b.name} ({b.code})</option>)}</Select></Field>
            <Field label="Floor"><Select disabled={!f.building_id} value={f.floor_id} onChange={(e) => setF((s) => ({ ...s, floor_id: e.target.value, room_id: "", asset_id: "" }))}><option value="">Any</option>{floors.data?.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}</Select></Field>
            <Field label="Room"><Select disabled={!f.building_id} value={f.room_id} onChange={(e) => setF((s) => ({ ...s, room_id: e.target.value, asset_id: "" }))}><option value="">Any</option>{rooms.data?.map((r) => <option key={r.id} value={r.id}>{r.room_number}{r.name ? ` · ${r.name}` : ""}</option>)}</Select></Field>
            <Field label="Asset"><Select disabled={!f.room_id} value={f.asset_id} onChange={up("asset_id")}><option value="">Any</option>{assets.data?.map((a) => <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>)}</Select></Field>
            <Field label="Department"><Select value={f.department_id} onChange={up("department_id")}><option value="">Let the copilot route</option>{depts.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select></Field>
          </Card>
          {create.error && <p className="rounded-xl border border-black px-3.5 py-2.5 text-sm">{(create.error as Error).message}</p>}
          <div className="flex gap-2"><Button type="submit" loading={create.isPending} className="flex-1">Submit report</Button><Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button></div>
        </div>
      </form>
    </div>
  );
}

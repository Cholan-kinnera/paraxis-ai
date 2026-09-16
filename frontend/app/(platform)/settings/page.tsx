"use client";
import { useCampuses, useProfile, useRoles, useSLAs } from "@/lib/hooks";
import { fmtDate, title } from "@/lib/utils";
import { Badge, Card, CardTitle, KV, PageHeader, Rows } from "@/components/platform/ui";

// DRF DurationField → "[D day(s), ]HH:MM:SS"
const hrs = (v?: string | number) => {
  if (v == null) return "—";
  const m = String(v).match(/(?:(\d+) days?, )?(\d+):(\d+):(\d+)/);
  if (!m) return String(v);
  const h = (+(m[1] ?? 0)) * 24 + +m[2], min = +m[3];
  return h ? `${h}h${min ? ` ${min}m` : ""}` : `${min}m`;
};

export default function SettingsPage() {
  const me = useProfile(); const slas = useSLAs(); const campuses = useCampuses(); const roles = useRoles();
  return (
    <div className="space-y-8">
      <PageHeader eyebrow="Workspace" title="Settings" sub="Identity, tenancy, roles and service levels for this campus." />
      <div className="grid gap-4 xl:grid-cols-2 [&>*]:min-w-0">
        <Card>
          <CardTitle>Profile</CardTitle>
          {me.isLoading ? <Rows n={4} /> : <KV items={[["Name", me.data?.full_name], ["Email", me.data?.email], ["Organization", me.data?.organization?.name], ["Campus", me.data?.primary_campus?.name], ["Roles", <div key="r" className="flex flex-wrap gap-1.5">{me.data?.roles.map((r) => <Badge key={r} value={r} />)}</div>], ["Member since", fmtDate(me.data?.created_at)]]} />}
        </Card>
        <Card>
          <CardTitle>Permissions</CardTitle>
          <div className="flex flex-wrap gap-1.5">{(me.data?.permissions ?? []).map((p) => <span key={p} className="rounded-full border border-neutral-300 px-2.5 py-1 font-mono text-[10.5px] text-neutral-700">{p}</span>)}</div>
        </Card>
        <Card>
          <CardTitle>Service levels</CardTitle>
          {slas.isLoading ? <Rows n={3} /> : <ul className="divide-y divide-neutral-100">{(slas.data ?? []).map((s) => <li key={s.id} className="flex items-center justify-between gap-3 py-3 text-sm"><div><div className="font-medium">{s.name}</div><div className="font-mono text-[10px] uppercase tracking-[0.14em] text-neutral-500">{[s.priority, s.task_type, s.category].filter(Boolean).map(title).join(" · ") || "Any"}</div></div><div className="flex items-center gap-4 font-mono text-xs text-neutral-600"><span>resp {hrs(s.response_target)}</span><span>res {hrs(s.resolution_target)}</span><Badge value={s.active ? "MET" : "CLOSED"} /></div></li>)}</ul>}
        </Card>
        <Card>
          <CardTitle>Tenancy</CardTitle>
          <div className="mb-3 font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500">Campuses</div>
          <ul className="space-y-2">{(campuses.data ?? []).map((c) => <li key={c.id} className="flex items-center justify-between rounded-xl border border-neutral-200 px-3.5 py-2.5 text-sm"><span>{c.name}</span><span className="font-mono text-xs text-neutral-500">{c.code}</span></li>)}</ul>
          <div className="mb-3 mt-6 font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500">Roles</div>
          <div className="flex flex-wrap gap-1.5">{(roles.data ?? []).map((r) => <Badge key={r.id} value={r.name} />)}</div>
        </Card>
      </div>
    </div>
  );
}

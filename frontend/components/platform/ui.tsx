"use client";
import Link from "next/link";
import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";
import { cn, title } from "@/lib/utils";

/* ---------- Badges (monochrome: intensity encodes severity) ---------- */
const tone: Record<string, string> = {
  // solid black = needs attention now
  CRITICAL: "bg-black text-white border-black", BREACHED: "bg-black text-white border-black", ESCALATED: "bg-black text-white border-black", BLOCKED: "bg-black text-white border-black", PENDING_APPROVAL: "bg-black text-white border-black",
  // dark outline = active
  HIGH: "border-black text-black", IN_PROGRESS: "border-black text-black", AT_RISK: "border-black text-black", TRIAGING: "border-black text-black", ASSIGNED: "border-black/60 text-black",
  // resolved / done
  RESOLVED: "bg-neutral-100 text-neutral-700 border-neutral-200", VERIFIED: "bg-neutral-100 text-neutral-700 border-neutral-200", CLOSED: "bg-neutral-100 text-neutral-500 border-neutral-200", COMPLETED: "bg-neutral-100 text-neutral-700 border-neutral-200", MET: "bg-neutral-100 text-neutral-700 border-neutral-200", HEALTHY: "bg-neutral-100 text-neutral-700 border-neutral-200",
};
export function Badge({ value, className, dot }: { value?: string | null; className?: string; dot?: boolean }) {
  if (!value) return <span className="text-neutral-400">—</span>;
  const attention = ["CRITICAL", "BREACHED", "ESCALATED", "PENDING_APPROVAL"].includes(value);
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-neutral-300 px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-[0.14em] text-neutral-600", tone[value], className)}>
      {(dot ?? attention) && <span className="relative flex h-1.5 w-1.5"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" /><span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-current" /></span>}
      {title(value)}
    </span>
  );
}

/* ---------- Buttons ---------- */
type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "outline" | "ghost" | "danger"; size?: "sm" | "md"; loading?: boolean; href?: string };
const btnBase = "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2";
const btnVar = {
  primary: "bg-black text-white hover:bg-neutral-800 active:scale-[0.98]",
  outline: "border border-neutral-300 bg-white text-black hover:border-black active:scale-[0.98]",
  ghost: "text-neutral-600 hover:bg-neutral-100 hover:text-black",
  danger: "border border-neutral-300 bg-white text-black hover:border-black hover:bg-black hover:text-white",
};
const btnSize = { sm: "h-8 px-3.5 text-[13px]", md: "h-10 px-5 text-sm" };
export const Button = forwardRef<HTMLButtonElement, BtnProps>(function Button({ className, variant = "primary", size = "md", loading, children, href, ...rest }, ref) {
  const cls = cn(btnBase, btnVar[variant], btnSize[size], className);
  if (href) return <Link href={href} className={cls}>{children}</Link>;
  return <button ref={ref} className={cls} disabled={loading || rest.disabled} {...rest}>{loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}{children}</button>;
});

/* ---------- Form controls ---------- */
const field = "w-full rounded-xl border border-neutral-300 bg-white px-3.5 py-2.5 text-sm text-black placeholder:text-neutral-400 transition-colors focus:border-black focus:outline-none disabled:bg-neutral-50";
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input({ className, ...p }, ref) { return <input ref={ref} className={cn(field, className)} {...p} />; });
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea({ className, ...p }, ref) { return <textarea ref={ref} className={cn(field, "min-h-[120px] resize-y leading-relaxed", className)} {...p} />; });
const chevron = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2'><path d='m6 9 6 6 6-6'/></svg>")`;
export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select({ className, children, style, ...p }, ref) {
  return <select ref={ref} className={cn(field, "appearance-none pr-9", className)} style={{ backgroundImage: chevron, backgroundRepeat: "no-repeat", backgroundPosition: "right 12px center", backgroundSize: "12px", ...style }} {...p}>{children}</select>;
});
export function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500">{label}</span>{children}{hint && <span className="mt-1.5 block text-xs text-neutral-500">{hint}</span>}</label>;
}

/* ---------- Layout ---------- */
export function PageHeader({ eyebrow, title: t, sub, actions }: { eyebrow?: string; title: React.ReactNode; sub?: React.ReactNode; actions?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 border-b border-neutral-200 pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <div className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-neutral-500">{eyebrow}</div>}
        <h1 className="mt-1 text-3xl font-medium tracking-tightest text-black sm:text-4xl">{t}</h1>
        {sub && <p className="mt-2 max-w-2xl text-sm text-neutral-500">{sub}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
export function Card({ children, className, pad = true }: { children: React.ReactNode; className?: string; pad?: boolean }) {
  return <div className={cn("rounded-2xl border border-neutral-200 bg-white", pad && "p-5", className)}>{children}</div>;
}
export function CardTitle({ children, action }: { children: React.ReactNode; action?: React.ReactNode }) {
  return <div className="mb-4 flex items-center justify-between"><h3 className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-neutral-500">{children}</h3>{action}</div>;
}
export function Stat({ label, value, delta, href }: { label: string; value: React.ReactNode; delta?: string; href?: string }) {
  const inner = (
    <div className="group rounded-2xl border border-neutral-200 bg-white p-5 transition-colors hover:border-black">
      <div className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-neutral-500">{label}</div>
      <div className="mt-3 text-4xl font-medium tracking-tightest text-black">{value}</div>
      {delta && <div className="mt-1.5 text-xs text-neutral-500">{delta}</div>}
    </div>
  );
  return href ? <Link href={href}>{inner}</Link> : inner;
}
export function Empty({ title: t, body, action }: { title: string; body?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-neutral-300 px-6 py-16 text-center">
      <div className="h-10 w-10 rounded-full border border-neutral-300" />
      <div className="mt-4 text-base font-medium text-black">{t}</div>
      {body && <p className="mt-1 max-w-sm text-sm text-neutral-500">{body}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
export function ErrorBox({ error, retry }: { error: unknown; retry?: () => void }) {
  const msg = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <div className="flex items-center justify-between rounded-2xl border border-black bg-white px-5 py-4 text-sm">
      <span><span className="font-mono text-[10.5px] uppercase tracking-[0.16em]">Error</span> · {msg}</span>
      {retry && <Button size="sm" variant="outline" onClick={retry}>Retry</Button>}
    </div>
  );
}
export function Skeleton({ className }: { className?: string }) { return <div className={cn("animate-pulse rounded-xl bg-neutral-100", className)} />; }
export function Rows({ n = 6 }: { n?: number }) { return <div className="space-y-2">{Array.from({ length: n }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>; }

/* ---------- Table ---------- */
export function Table({ head, children, className }: { head: (string | React.ReactNode)[]; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-x-auto rounded-2xl border border-neutral-200 bg-white", className)}>
      <table className="w-full min-w-[720px] text-sm">
        <thead><tr className="border-b border-neutral-200">{head.map((h, i) => <th key={i} className="px-4 py-3 text-left font-mono text-[10.5px] font-normal uppercase tracking-[0.16em] text-neutral-500">{h}</th>)}</tr></thead>
        <tbody className="divide-y divide-neutral-100">{children}</tbody>
      </table>
    </div>
  );
}
export const Td = ({ children, className }: { children: React.ReactNode; className?: string }) => <td className={cn("px-4 py-3.5 align-middle text-black", className)}>{children}</td>;

/* ---------- Key/Value ---------- */
export function KV({ items }: { items: [string, React.ReactNode][] }) {
  return (
    <dl className="divide-y divide-neutral-100">
      {items.map(([k, v]) => (
        <div key={k} className="grid grid-cols-[140px_1fr] gap-4 py-2.5 text-sm"><dt className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500 leading-5">{k}</dt><dd className="text-black">{v ?? <span className="text-neutral-400">—</span>}</dd></div>
      ))}
    </dl>
  );
}

/* ---------- Timeline ---------- */
export function Timeline({ items }: { items: { id: string; label: string; body?: string; meta?: string; when: string; actor?: string }[] }) {
  if (!items.length) return <p className="text-sm text-neutral-500">No events yet.</p>;
  return (
    <ol className="relative ml-2 border-l border-neutral-200">
      {items.map((e, i) => (
        <li key={e.id} className="relative pb-6 pl-6 last:pb-0">
          <span className={cn("absolute -left-[5px] top-1.5 h-2.5 w-2.5 rounded-full border border-black", i === 0 ? "bg-black" : "bg-white")} />
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <span className="text-sm font-medium text-black">{e.label}</span>
            <span className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-neutral-400">{e.when}</span>
          </div>
          {e.body && <p className="mt-1 text-sm text-neutral-600">{e.body}</p>}
          {(e.actor || e.meta) && <p className="mt-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-neutral-400">{[e.actor, e.meta].filter(Boolean).join(" · ")}</p>}
        </li>
      ))}
    </ol>
  );
}

/* ---------- Drawer ---------- */
export function Drawer({ open, onClose, title: t, children, footer }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode; footer?: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50">
      <button aria-label="Close" onClick={onClose} className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-lg flex-col bg-white shadow-2xl animate-[rise_0.35s_cubic-bezier(0.16,1,0.3,1)]">
        <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4"><h2 className="text-lg font-medium tracking-tight">{t}</h2><Button variant="ghost" size="sm" onClick={onClose}>Close</Button></div>
        <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
        {footer && <div className="border-t border-neutral-200 px-6 py-4">{footer}</div>}
      </aside>
    </div>
  );
}

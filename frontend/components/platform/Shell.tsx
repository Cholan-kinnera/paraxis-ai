"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { LayoutGrid, AlertTriangle, ListChecks, Map, Bot, Settings, LogOut, Plus, Search, Menu, X, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { auth } from "@/lib/auth";
import { useProfile } from "@/lib/hooks";
import { Logo } from "@/components/Logo";

const nav = [
  { href: "/dashboard", label: "Command Center", icon: LayoutGrid },
  { href: "/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/tasks", label: "Tasks & SLAs", icon: ListChecks },
  { href: "/campus", label: "Campus Graph", icon: Map },
  { href: "/agent", label: "Agent Copilot", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [open, setOpen] = useState(false);
  const { data: me } = useProfile();

  useEffect(() => {
    if (!auth.access) router.replace(`/login?next=${encodeURIComponent(path)}`);
    else setReady(true);
  }, [path, router]);
  useEffect(() => { setOpen(false); }, [path]);

  const user = me ?? auth.user;
  const logout = () => { auth.clear(); router.replace("/login"); };
  const crumbs = path.split("/").filter(Boolean);

  if (!ready) return <div className="theme-light min-h-screen bg-white" />;
  return (
    <div className="theme-light min-h-screen bg-white text-black">
      {/* Sidebar */}
      <aside className={cn("fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-neutral-200 bg-white transition-transform duration-300 lg:translate-x-0", open ? "translate-x-0" : "-translate-x-full")}>
        <div className="flex h-16 items-center justify-between border-b border-neutral-200 px-5">
          <Link href="/dashboard" className="flex items-center gap-2.5"><Logo className="h-6 w-6" /><span className="text-[15px] font-semibold tracking-tight">Paraxis<span className="text-neutral-400"> AI</span></span></Link>
          <button className="lg:hidden" onClick={() => setOpen(false)} aria-label="Close menu"><X className="h-5 w-5" /></button>
        </div>
        <div className="px-3 pt-4">
          <Link href="/incidents/new" className="flex h-10 items-center justify-center gap-2 rounded-full bg-black text-sm font-medium text-white transition-colors hover:bg-neutral-800"><Plus className="h-4 w-4" />Report Incident</Link>
        </div>
        <nav className="mt-4 flex-1 space-y-0.5 px-3">
          {nav.map((n) => {
            const active = path === n.href || path.startsWith(n.href + "/");
            return (
              <Link key={n.href} href={n.href} className={cn("group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors", active ? "bg-black text-white" : "text-neutral-600 hover:bg-neutral-100 hover:text-black")}>
                <n.icon className="h-4 w-4" strokeWidth={1.8} />{n.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-neutral-200 p-3">
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-black font-mono text-xs text-white">{(user?.full_name ?? "?").split(" ").map((s) => s[0]).slice(0, 2).join("")}</div>
            <div className="min-w-0 flex-1"><div className="truncate text-sm font-medium">{user?.full_name ?? "—"}</div><div className="truncate font-mono text-[10px] uppercase tracking-wider text-neutral-500">{user?.roles?.[0]?.replace(/_/g, " ") ?? "user"}</div></div>
            <button onClick={logout} aria-label="Sign out" className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 hover:text-black"><LogOut className="h-4 w-4" /></button>
          </div>
        </div>
      </aside>
      {open && <button aria-label="Close" className="fixed inset-0 z-30 bg-black/20 lg:hidden" onClick={() => setOpen(false)} />}

      {/* Main */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-neutral-200 bg-white/80 px-4 backdrop-blur-xl sm:px-8">
          <button className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu"><Menu className="h-5 w-5" /></button>
          <nav className="hidden items-center gap-1.5 font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500 sm:flex">
            {crumbs.map((c, i) => <span key={i} className="flex items-center gap-1.5">{i > 0 && <ChevronRight className="h-3 w-3" />}<span className={cn(i === crumbs.length - 1 && "text-black")}>{c.length > 12 ? c.slice(0, 8) + "…" : c.replace(/-/g, " ")}</span></span>)}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-neutral-200 px-3 py-1.5 text-xs text-neutral-500 md:flex"><Search className="h-3.5 w-3.5" />Search<kbd className="ml-2 rounded border border-neutral-200 px-1 font-mono text-[10px]">⌘K</kbd></div>
            <span className="flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.18em] text-neutral-500"><span className="h-1.5 w-1.5 rounded-full bg-black" />Live</span>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-8">{children}</main>
      </div>
    </div>
  );
}

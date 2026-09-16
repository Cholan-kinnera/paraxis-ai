"use client";
import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { useLogin } from "@/lib/hooks";
import { Button, Field, Input } from "@/components/platform/ui";
import { Logo } from "@/components/Logo";

const demo = [["campus.admin@apex.edu", "Campus Admin"], ["technician@apex.edu", "Technician"], ["student.eng@apex.edu", "Student"]];

function LoginForm() {
  const router = useRouter();
  const next = useSearchParams().get("next") || "/dashboard";
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const submit = (e: React.FormEvent) => { e.preventDefault(); login.mutate({ email, password }, { onSuccess: () => router.replace(next) }); };
  return (
    <form onSubmit={submit} className="w-full max-w-sm">
      <Link href="/" className="flex items-center gap-2.5"><Logo className="h-7 w-7" /><span className="text-lg font-semibold tracking-tight">Paraxis AI</span></Link>
      <h1 className="mt-12 text-4xl font-medium tracking-tightest">Welcome back.</h1>
      <p className="mt-2 text-sm text-neutral-500">Sign in to your campus command center.</p>
      <div className="mt-8 space-y-4">
        <Field label="Email"><Input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@campus.edu" /></Field>
        <Field label="Password"><Input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••••" /></Field>
      </div>
      {login.error && <p className="mt-4 rounded-xl border border-black px-3.5 py-2.5 text-sm">{(login.error as Error).message}</p>}
      <Button type="submit" loading={login.isPending} className="mt-6 w-full">Sign in <ArrowRight className="h-4 w-4" /></Button>
      <div className="mt-10 border-t border-neutral-200 pt-6">
        <div className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-neutral-500">Development accounts</div>
        <div className="mt-3 flex flex-wrap gap-2">
          {demo.map(([e, r]) => <button type="button" key={e} onClick={() => { setEmail(e); setPassword("DevPassword123!"); }} className="rounded-full border border-neutral-300 px-3 py-1.5 text-xs text-neutral-700 transition-colors hover:border-black hover:text-black">{r}</button>)}
        </div>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <div className="theme-light grid min-h-screen bg-white text-black lg:grid-cols-2">
      <div className="flex items-center justify-center px-6 py-16"><Suspense><LoginForm /></Suspense></div>
      <div className="relative hidden overflow-hidden bg-black text-white lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="grid-lines absolute inset-0 opacity-60" />
        <div className="absolute -bottom-40 left-1/2 h-[640px] w-[640px] -translate-x-1/2 rounded-full border border-white/10" />
        <div className="absolute -bottom-64 left-1/2 h-[900px] w-[900px] -translate-x-1/2 rounded-full border border-white/[0.06]" />
        <div className="relative font-mono text-[11px] uppercase tracking-[0.25em] text-white/40">The Intelligent Operational Layer</div>
        <div className="relative">
          <p className="text-4xl font-medium leading-[1.05] tracking-tightest xl:text-5xl">See what is happening.<br />Understand what matters.<br /><span className="font-serif italic text-white/80">Coordinate what happens next.</span></p>
          <div className="mt-10 grid grid-cols-3 gap-6 border-t border-white/10 pt-6">
            {[["12 min", "median dispatch"], ["100%", "policy gated"], ["0", "unaudited actions"]].map(([v, l]) => <div key={l}><div className="text-2xl font-medium tracking-tight">{v}</div><div className="mt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-white/40">{l}</div></div>)}
          </div>
        </div>
      </div>
    </div>
  );
}

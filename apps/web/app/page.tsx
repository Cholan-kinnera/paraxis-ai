export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 md:p-16 max-w-6xl mx-auto">
      {/* Top Header */}
      <header className="w-full flex justify-between items-center pb-8 border-b border-border/60">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-brand-primary/20 border border-brand-primary flex items-center justify-center font-mono font-bold text-brand-primary">
            PX
          </div>
          <div>
            <h1 className="font-semibold tracking-tight text-foreground text-lg">PARAXIS AI</h1>
            <p className="text-xs text-muted-foreground">The Intelligent Operational Layer for Modern Campuses</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center rounded-full bg-status-operational/10 px-2.5 py-0.5 text-xs font-medium text-status-operational border border-status-operational/20">
            <span className="h-1.5 w-1.5 rounded-full bg-status-operational mr-1.5 animate-pulse" />
            Foundation Active
          </span>
        </div>
      </header>

      {/* Hero Core Promise */}
      <section className="my-16 text-center max-w-3xl">
        <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-6">
          See what is happening.<br />
          <span className="text-brand-primary">Understand what matters.</span><br />
          Coordinate what happens next.
        </h2>
        <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
          Paraxis AI sits above fragmented campus workflows to detect problems, understand operational context,
          coordinate cross-functional dispatches, monitor SLAs, and surface recurring systemic patterns.
        </p>
      </section>

      {/* Architecture Foundations Matrix */}
      <section className="w-full grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-foreground">Core Platform</h3>
            <span className="text-xs font-mono bg-border px-2 py-0.5 rounded text-muted-foreground">apps/core</span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            Django 5 + DRF sovereign domain authority. Governs organizations, campuses, canonical business state, and immutable audit trails.
          </p>
          <div className="text-xs font-mono text-status-operational flex items-center">
            • Port 8000: PostgreSQL 16 + pgvector
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-foreground">Intelligence Engine</h3>
            <span className="text-xs font-mono bg-border px-2 py-0.5 rounded text-muted-foreground">apps/intelligence</span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            FastAPI + LangGraph stateful orchestrator. Executes 13-node cognitive loops, operational RAG, and typed tool contracts.
          </p>
          <div className="text-xs font-mono text-status-agent flex items-center">
            • Port 8001: Model Gateway + SSE
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-foreground">Policy Engine</h3>
            <span className="text-xs font-mono bg-border px-2 py-0.5 rounded text-muted-foreground">Deterministic Gate</span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            The LLM proposes; the Policy Engine decides. Automatic dispatches for routine tasks; mandatory human approvals for sensitive actions.
          </p>
          <div className="text-xs font-mono text-status-triaging flex items-center">
            • ALLOW | APPROVAL | DENY
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full pt-8 border-t border-border/40 text-center text-xs text-muted-foreground flex justify-between items-center">
        <span>Paraxis AI Foundation Initialized • Monorepo Architecture</span>
        <span className="font-mono">v0.1.0-alpha</span>
      </footer>
    </main>
  );
}

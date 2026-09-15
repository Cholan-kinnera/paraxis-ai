import React from "react";

export interface StatusBadgeProps {
  children: React.ReactNode;
  variant?: "operational" | "triaging" | "critical" | "agent" | "neutral";
  pulse?: boolean;
  className?: string;
}

export function StatusBadge({
  children,
  variant = "operational",
  pulse = true,
  className = "",
}: StatusBadgeProps) {
  const variantStyles = {
    operational: {
      badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      dot: "bg-emerald-400",
    },
    triaging: {
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      dot: "bg-amber-400",
    },
    critical: {
      badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
      dot: "bg-rose-400",
    },
    agent: {
      badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      dot: "bg-cyan-400",
    },
    neutral: {
      badge: "bg-white/[0.05] text-slate-300 border-white/10",
      dot: "bg-slate-400",
    },
  }[variant];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-mono tracking-wider uppercase border select-none ${variantStyles.badge} ${className}`}
    >
      <span className="relative flex h-1.5 w-1.5 mr-1.5">
        {pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${variantStyles.dot}`}
          />
        )}
        <span
          className={`relative inline-flex rounded-full h-1.5 w-1.5 ${variantStyles.dot}`}
        />
      </span>
      {children}
    </span>
  );
}

import React from "react";

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  elevated?: boolean;
  hoverGlow?: boolean;
  className?: string;
}

export function GlassCard({
  children,
  elevated = false,
  hoverGlow = true,
  className = "",
  ...props
}: GlassCardProps) {
  return (
    <div
      className={`relative rounded-2xl transition-all duration-300 ${
        elevated ? "glass-panel-elevated" : "glass-panel"
      } ${
        hoverGlow
          ? "hover:border-brand-cyan/35 hover:shadow-[0_0_30px_-8px_rgba(6,182,212,0.15)]"
          : ""
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

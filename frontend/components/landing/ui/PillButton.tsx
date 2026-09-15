import React from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export interface PillButtonProps {
  children: React.ReactNode;
  href?: string;
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: boolean;
  className?: string;
  onClick?: () => void;
}

export function PillButton({
  children,
  href,
  variant = "primary",
  size = "md",
  icon = true,
  className = "",
  onClick,
}: PillButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-brand-cyan/40 disabled:opacity-50 select-none min-h-[44px]";

  const sizeStyles = {
    sm: "text-xs px-4 py-2 gap-1.5",
    md: "text-sm px-5 py-2.5 gap-2",
    lg: "text-base px-7 py-3.5 gap-2.5",
  }[size];

  const variantStyles = {
    primary:
      "bg-white text-black hover:bg-slate-100 shadow-[0_0_20px_-3px_rgba(255,255,255,0.4)] hover:shadow-[0_0_25px_-1px_rgba(255,255,255,0.6)] active:scale-[0.98]",
    secondary:
      "bg-white/[0.08] text-slate-200 border border-white/[0.12] hover:bg-white/[0.14] hover:border-white/20 active:scale-[0.98] backdrop-blur-md",
    outline:
      "bg-transparent text-slate-300 border border-white/[0.15] hover:border-brand-cyan/50 hover:text-white hover:bg-brand-cyan/[0.05] active:scale-[0.98]",
    ghost:
      "bg-transparent text-slate-400 hover:text-white hover:bg-white/[0.05]",
  }[variant];

  const content = (
    <>
      <span>{children}</span>
      {icon && (
        <ArrowUpRight className="h-4 w-4 shrink-0 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      )}
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        className={`group ${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
      >
        {content}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group ${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
    >
      {content}
    </button>
  );
}

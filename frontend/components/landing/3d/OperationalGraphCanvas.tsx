"use client";

import React, { useState, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { OperationalGraphScene } from "./OperationalGraphScene";

interface OperationalGraphCanvasProps {
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
}

export function OperationalGraphCanvas({
  selectedNodeId,
  onSelectNode,
}: OperationalGraphCanvasProps) {
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
      const listener = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
      mediaQuery.addEventListener("change", listener);

      const observer = new IntersectionObserver(
        ([entry]) => {
          setIsVisible(entry.isIntersecting);
        },
        { threshold: 0.05 }
      );

      if (containerRef.current) {
        observer.observe(containerRef.current);
      }

      return () => {
        mediaQuery.removeEventListener("change", listener);
        observer.disconnect();
      };
    }
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[420px] sm:h-[500px] lg:h-[540px] rounded-2xl overflow-hidden bg-[#030712]/90 border border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] cursor-grab active:cursor-grabbing"
    >
      {/* 3D Scene Controls Badge */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 pointer-events-none">
        <div className="px-2.5 py-1 rounded-full bg-black/60 border border-brand-cyan/30 backdrop-blur-md text-[10px] font-mono text-cyan-300">
          ✦ 3D SPATIAL MODEL · DRAG TO ORBIT
        </div>
      </div>

      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-2 pointer-events-none">
        <div className="px-2.5 py-1 rounded-full bg-black/60 border border-white/10 backdrop-blur-md text-[10px] font-mono text-slate-400">
          CLICK NODE TO INSPECT ANCESTRY
        </div>
      </div>

      <Canvas
        frameloop={isVisible ? "always" : "never"}
        camera={{ position: [3.5, 2.8, 4.5], fov: 45, near: 0.1, far: 50 }}
        dpr={[1, typeof window !== "undefined" ? Math.min(window.devicePixelRatio, 1.75) : 1]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
        }}
        className="w-full h-full"
      >
        <OperationalGraphScene
          selectedNodeId={selectedNodeId}
          onSelectNode={onSelectNode}
          reducedMotion={reducedMotion}
        />
      </Canvas>
    </div>
  );
}

export default OperationalGraphCanvas;

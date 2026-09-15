"use client";

import React, { useState, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { HeroCampusScene } from "./HeroCampusScene";

export function HeroCampusCanvas() {
  const [reducedMotion, setReducedMotion] = useState<boolean>(false);
  const [isVisible, setIsVisible] = useState<boolean>(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Detect OS reduced motion preference
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
      const listener = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
      mediaQuery.addEventListener("change", listener);

      // Visibility observer to save battery/GPU when hero is scrolled out of viewport
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
      className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden select-none -z-10"
      aria-hidden="true"
    >
      <Canvas
        frameloop={isVisible ? "always" : "never"}
        camera={{ position: [3.8, 2.0, 5.8], fov: 42, near: 0.1, far: 50 }}
        dpr={[1, typeof window !== "undefined" ? Math.min(window.devicePixelRatio, 1.75) : 1]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
        }}
        className="w-full h-full pointer-events-none"
      >
        <HeroCampusScene reducedMotion={reducedMotion} />
      </Canvas>
    </div>
  );
}

export default HeroCampusCanvas;

"use client";
import { useEffect, useRef, type MutableRefObject } from "react";
import * as THREE from "three";

/** Target pose for the sphere. */
export interface Stage { position: THREE.Vector3; radius: number; tiltX: number; tiltZ: number; opacity: number; spin: number }

type Pose = { x: number; y: number; z: number; r: number; tx: number; tz: number; o: number; spin: number };
const smooth = (v: number) => { const t = Math.min(1, Math.max(0, v)); return t * t * (3 - 2 * t); };
const L = (a: number, b: number, u: number) => a + (b - a) * u;

// Camera: z 24, fov 30 → 1 world unit ≈ 0.155 NDC at z 0; viewport half-width in world units = 6.43 * aspect.
const CAM_Z = 24, TAN = Math.tan((30 * Math.PI) / 360);

/**
 * One continuous journey, keyed to section anchors (document order). The object never disappears:
 * hero bowl → recedes behind the feature cards → weaves left/right opposite the copy in the showcase rows,
 * tilting a little more each time → sinks behind the stats → drifts right and rolls pole-on into the footer vortex.
 * x / r are in "desktop units" and scaled for narrow viewports.
 */
const KEYS: { id: string; edge?: "top" | "center" | "bottom"; pose: Pose }[] = [
  { id: "hero", edge: "top",       pose: { x: 0,    y: 0,    z: 3,   r: 12.5, tx: 0,    tz: 0,     o: 1,    spin: 0.04 } }, // y is set from the CTA anchor
  { id: "hero", edge: "bottom",    pose: { x: 0,    y: 0,    z: -14, r: 6,    tx: 0.2,  tz: 0.05,  o: 0.6,  spin: 0.06 } }, // rides up with the page while receding (y from the CTA anchor)
  { id: "product",                 pose: { x: 0,    y: 3.4,  z: -20, r: 5,    tx: 0.15, tz: 0.1,   o: 0.5,  spin: 0.08 } }, // rises as a distant globe behind the heading
  { id: "platform",                pose: { x: 7,    y: 0.5,  z: -14, r: 4.6,  tx: 0.45, tz: -0.2,  o: 0.65, spin: 0.1 } },
  { id: "report",                  pose: { x: -7,   y: 0.2,  z: -14, r: 4.6,  tx: 0.8,  tz: 0.25,  o: 0.65, spin: 0.12 } },
  { id: "workflow",                pose: { x: 7,    y: 0.4,  z: -14, r: 4.6,  tx: 1.1,  tz: -0.25, o: 0.65, spin: 0.14 } },
  { id: "governance",              pose: { x: 0,    y: 4.6,  z: -22, r: 5.5,  tx: 0.6,  tz: 0.1,   o: 0.4,  spin: 0.1 } },
  { id: "proof",                   pose: { x: -9.5, y: -2,   z: -16, r: 5,    tx: 0.35, tz: 0.2,   o: 0.5,  spin: 0.1 } },
  { id: "stats",                   pose: { x: -2.6, y: 1.2,  z: -6,  r: 5.2,  tx: 0.3,  tz: -0.15, o: 0.5,  spin: 0.12 } },
  { id: "pricing",                 pose: { x: 8.5,  y: 2,    z: -14, r: 5,    tx: 1.0,  tz: 0.3,   o: 0.5,  spin: 0.2 } },
  { id: "final",                   pose: { x: 7.4,  y: 0.8,  z: 0,   r: 6.2,  tx: Math.PI / 2, tz: 0.4, o: 1, spin: 0.3 } }, // x is multiplied by aspect
];

export function useSceneStage(): MutableRefObject<Stage> {
  const ref = useRef<Stage>({ position: new THREE.Vector3(0, -12, 3), radius: 12.5, tiltX: 0, tiltZ: 0, opacity: 0, spin: 0.05 });
  useEffect(() => {
    const el = (id: string) => document.getElementById(id);
    let raf = 0;
    const tick = () => {
      const vh = window.innerHeight, vw = window.innerWidth, aspect = vw / vh;
      const narrow = Math.min(1, Math.max(0.42, aspect / 1.78)); // scale side offsets + radii on phones
      const focus = window.scrollY + vh / 2;

      // Anchor each key to a point of its section in document space (default: its centre). The focus line is the viewport centre.
      const pts = KEYS.map((k) => {
        const r = el(k.id)?.getBoundingClientRect();
        if (!r) return { at: Infinity, pose: { ...k.pose } };
        const top = window.scrollY + r.top;
        const at = k.edge === "top" ? top + vh / 2 : k.edge === "bottom" ? top + r.height : top + r.height / 2;
        return { at, pose: { ...k.pose } };
      }).filter((p) => Number.isFinite(p.at));
      if (!pts.length) return;

      // Hero pose: pole a fixed gap under the CTA group (projected from px → world units at z 3).
      const cta = el("hero-cta")?.getBoundingClientRect();
      if (cta) {
        const ndc = 1 - (2 * (cta.bottom + vh * 0.06)) / vh;
        for (const p of pts.slice(0, 2)) p.pose.y = ndc * (CAM_Z - p.pose.z) * TAN - p.pose.r;
      }
      // Viewport adaptation: middle keys shrink and hug the edges on narrow screens; the footer key anchors to the right edge.
      pts.forEach((p, idx) => {
        if (idx === 0) return;
        if (idx === pts.length - 1) {
          if (aspect > 1) p.pose.x *= aspect;
          else Object.assign(p.pose, { x: 5.8, y: -4.6, r: 3.2, o: 0.75 });
          return;
        }
        p.pose.x *= narrow; p.pose.r *= narrow;
      });

      let i = 0;
      while (i < pts.length - 2 && focus > pts[i + 1].at) i++;
      const a = pts[i], b = pts[i + 1];
      const u = smooth((focus - a.at) / Math.max(1, b.at - a.at));
      const A = a.pose, B = b.pose;
      const s = ref.current;
      s.position.set(L(A.x, B.x, u), L(A.y, B.y, u), L(A.z, B.z, u));
      s.radius = L(A.r, B.r, u);
      s.tiltX = L(A.tx, B.tx, u);
      s.tiltZ = L(A.tz, B.tz, u);
      s.opacity = L(A.o, B.o, u);
      s.spin = L(A.spin, B.spin, u);
    };
    const loop = () => { tick(); raf = requestAnimationFrame(loop); };
    loop();
    return () => cancelAnimationFrame(raf);
  }, []);
  return ref;
}

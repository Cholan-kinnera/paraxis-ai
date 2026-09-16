"use client";
import { useEffect, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { Stage } from "./stage";

interface Props {
  stage: React.MutableRefObject<Stage>;
  color?: string;
  rings?: number;      // latitude rows
  density?: number;    // dashes around the equator
}

/**
 * A sphere built from a lattice of short glowing dashes, one InstancedMesh (one draw call).
 * Dashes lie along their latitude row, like the reference model.
 */
export function DashSphere({ stage, color = "#ffffff", rings = 72, density = 140 }: Props) {
  const ref = useRef<THREE.InstancedMesh>(null);
  const spin = useRef(0);

  const { count, matrices, colors } = useMemo(() => {
    const dummy = new THREE.Object3D();
    const up = new THREE.Vector3(0, 1, 0);
    const list: THREE.Matrix4[] = [];
    const cols: number[] = [];
    const c = new THREE.Color(color);
    for (let r = 1; r < rings; r++) {
      const lat = -Math.PI / 2 + (r / rings) * Math.PI;
      const cosL = Math.cos(lat);
      const n = Math.max(6, Math.round(density * cosL));
      const rowGlow = 0.6 + 0.4 * Math.random(); // whole-row brightness variation like the reference
      for (let i = 0; i < n; i++) {
        const lon = (i / n) * Math.PI * 2 + (r % 2) * (Math.PI / n);
        const p = new THREE.Vector3(cosL * Math.cos(lon), Math.sin(lat), cosL * Math.sin(lon));
        const east = new THREE.Vector3(-Math.sin(lon), 0, Math.cos(lon)); // tangent along the row
        dummy.position.copy(p);
        dummy.quaternion.setFromUnitVectors(up, east);
        dummy.scale.setScalar(1);
        dummy.updateMatrix();
        list.push(dummy.matrix.clone());
        const b = rowGlow * (0.55 + 0.6 * Math.random());
        cols.push(c.r * b, c.g * b, c.b * b);
      }
    }
    return { count: list.length, matrices: list, colors: new Float32Array(cols) };
  }, [rings, density, color]);

  useEffect(() => {
    const m = ref.current;
    if (!m) return;
    matrices.forEach((mat, i) => m.setMatrixAt(i, mat));
    m.instanceMatrix.needsUpdate = true;
    m.instanceColor = new THREE.InstancedBufferAttribute(colors, 3);
  }, [matrices, colors]);

  const material = useMemo(
    () => new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }),
    [],
  );

  useFrame((_, delta) => {
    const m = ref.current;
    if (!m) return;
    const s = stage.current;
    spin.current += delta * s.spin;
    const k = 1 - Math.exp(-delta * 3); // frame-rate independent smoothing
    m.position.lerp(s.position, k);
    m.scale.lerp(new THREE.Vector3(s.radius, s.radius, s.radius), k);
    m.rotation.x += (s.tiltX - m.rotation.x) * k;
    m.rotation.z += (s.tiltZ - m.rotation.z) * k;
    m.rotation.y = spin.current;
    material.opacity += (s.opacity - material.opacity) * k;
    m.visible = material.opacity > 0.01;
  });

  return (
    <instancedMesh ref={ref} args={[undefined, undefined, count]} material={material} frustumCulled={false}>
      <capsuleGeometry args={[0.004, 0.022, 2, 6]} />
    </instancedMesh>
  );
}

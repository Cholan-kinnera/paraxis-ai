"use client";

import React, { useRef, useMemo, useEffect } from "react";
import * as THREE from "three";
import { useFrame, useThree } from "@react-three/fiber";
import { CampusTopologyMesh } from "./CampusTopologyMesh";
import { ConnectionSplines } from "./ConnectionSplines";
import { IncidentBeaconNode } from "./IncidentBeaconNode";

interface HeroCampusSceneProps {
  reducedMotion?: boolean;
}

export function HeroCampusScene({ reducedMotion = false }: HeroCampusSceneProps) {
  const { camera } = useThree();
  const spotLight1Ref = useRef<THREE.SpotLight>(null);
  const spotLight2Ref = useRef<THREE.SpotLight>(null);
  const scrollRef = useRef<number>(0);

  // Monitor normalized window scroll progression
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY || window.pageYOffset;
      const heroHeight = window.innerHeight * 1.5;
      const progress = Math.min(Math.max(scrollY / heroHeight, 0), 1);
      scrollRef.current = progress;
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Background Telemetry Grid & Floor Coordinates
  const gridHelper = useMemo(() => {
    const grid = new THREE.GridHelper(24, 32, new THREE.Color("#00E5FF"), new THREE.Color("#0F172A"));
    grid.position.y = -1.6;
    if (Array.isArray(grid.material)) {
      grid.material.forEach((m) => {
        m.transparent = true;
        m.opacity = 0.18;
      });
    } else {
      grid.material.transparent = true;
      grid.material.opacity = 0.18;
    }
    return grid;
  }, []);

  // Spatial telemetry dust particles
  const particles = useMemo(() => {
    const count = 48;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 12;
      positions[i * 3 + 1] = Math.random() * 4 - 1.2;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: new THREE.Color("#38BDF8"),
      size: 0.035,
      transparent: true,
      opacity: 0.45,
    });
    return new THREE.Points(geom, mat);
  }, []);

  // Frame Loop: Smooth camera scroll choreography & pointer micro-parallax
  useFrame((state, delta) => {
    const progress = scrollRef.current;

    // Base start position: Wide cinematic angle [3.8, 2.0, 5.8]
    // Scrolled target position near command center: [1.4, 0.9, 3.4]
    const targetX = THREE.MathUtils.lerp(3.8, 1.4, progress);
    const targetY = THREE.MathUtils.lerp(2.0, 0.9, progress);
    const targetZ = THREE.MathUtils.lerp(5.8, 3.4, progress);

    // Subtle pointer parallax (constrained, avoiding nausea)
    const parallaxX = reducedMotion ? 0 : state.pointer.x * 0.35;
    const parallaxY = reducedMotion ? 0 : state.pointer.y * 0.25;

    // Smooth dampening towards target camera position
    camera.position.x = THREE.MathUtils.damp(camera.position.x, targetX + parallaxX, 4, delta);
    camera.position.y = THREE.MathUtils.damp(camera.position.y, targetY + parallaxY, 4, delta);
    camera.position.z = THREE.MathUtils.damp(camera.position.z, targetZ, 4, delta);

    // Target lookAt point shifts slightly to focus on the AP-204 incident beacon as you scroll
    const lookTargetX = THREE.MathUtils.lerp(0.2, 0.1, progress);
    const lookTargetY = THREE.MathUtils.lerp(0.3, 0.6, progress);
    const lookTargetZ = THREE.MathUtils.lerp(0.2, 0.4, progress);
    camera.lookAt(lookTargetX, lookTargetY, lookTargetZ);

    // Subtle spotlight movement for theatrical edge highlights
    if (!reducedMotion && spotLight1Ref.current) {
      const t = state.clock.getElapsedTime();
      spotLight1Ref.current.position.x = 4 + Math.sin(t * 0.4) * 0.5;
    }
  });

  return (
    <>
      {/* Cinematic Ambient Lighting (Restrained obsidian baseline) */}
      <ambientLight color="#050914" intensity={1.2} />

      {/* Theatrical Spotlight 1: Electric Cyan keylight casting onto campus topology */}
      <spotLight
        ref={spotLight1Ref}
        position={[4.5, 6.0, 4.0]}
        target-position={[0.2, 0.4, 0.2]}
        color="#00E5FF"
        intensity={18}
        angle={0.55}
        penumbra={0.85}
        distance={20}
        decay={1.8}
        castShadow
      />

      {/* Theatrical Spotlight 2: Cobalt/Indigo rimlight defining architectural depth */}
      <spotLight
        ref={spotLight2Ref}
        position={[-5.0, 4.5, -2.0]}
        target-position={[0.0, 0.0, 0.0]}
        color="#6366F1"
        intensity={14}
        angle={0.65}
        penumbra={0.9}
        distance={18}
        decay={2}
      />

      {/* Emerald Operational Health PointLight */}
      <pointLight
        position={[2.4, -0.2, 1.4]}
        color="#10B981"
        intensity={2.0}
        distance={4.5}
        decay={2}
      />

      {/* Background Spatial Grid & Particles */}
      <primitive object={gridHelper} />
      <primitive object={particles} />

      {/* Primary Campus Architectural Topology */}
      <CampusTopologyMesh reducedMotion={reducedMotion} />

      {/* Living Signal Conduits and Packets */}
      <ConnectionSplines reducedMotion={reducedMotion} />

      {/* AP-204 Active Incident Beacon at Room 101 */}
      <IncidentBeaconNode reducedMotion={reducedMotion} />
    </>
  );
}

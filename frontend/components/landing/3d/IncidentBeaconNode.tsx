"use client";

import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

interface IncidentBeaconNodeProps {
  reducedMotion?: boolean;
}

export function IncidentBeaconNode({ reducedMotion = false }: IncidentBeaconNodeProps) {
  const coreRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const outerGimbalRef = useRef<THREE.Group>(null);
  const pointLightRef = useRef<THREE.PointLight>(null);

  // Procedural geometries for technical beacon
  const geometries = useMemo(() => {
    return {
      core: new THREE.OctahedronGeometry(0.12, 0),
      outerRing: new THREE.TorusGeometry(0.24, 0.015, 12, 36),
      gimbalRing: new THREE.TorusGeometry(0.32, 0.01, 12, 36),
      pedestalPin: new THREE.CylinderGeometry(0.01, 0.02, 0.25, 8),
    };
  }, []);

  // Emissive materials
  const materials = useMemo(() => {
    return {
      beaconEmissive: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#00E5FF"),
        emissive: new THREE.Color("#00E5FF"),
        emissiveIntensity: 3.2,
        roughness: 0.1,
        metalness: 0.3,
      }),
      ringAccent: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#38BDF8"),
        emissive: new THREE.Color("#0284C7"),
        emissiveIntensity: 1.8,
        roughness: 0.2,
        metalness: 0.8,
      }),
      amberAlert: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#F59E0B"),
        emissive: new THREE.Color("#F59E0B"),
        emissiveIntensity: 1.5,
        roughness: 0.2,
        metalness: 0.5,
      }),
      pinDark: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#0F172A"),
        metalness: 0.9,
        roughness: 0.3,
      }),
    };
  }, []);

  // Beacon pulse and rotational gimbal animation
  useFrame((state) => {
    if (!coreRef.current || reducedMotion) return;
    const t = state.clock.getElapsedTime();

    // Subtle scale breathing on core
    const pulseScale = 1 + Math.sin(t * 3.5) * 0.15;
    coreRef.current.scale.set(pulseScale, pulseScale, pulseScale);
    coreRef.current.rotation.y = t * 1.2;
    coreRef.current.rotation.x = t * 0.8;

    if (ringRef.current) {
      ringRef.current.rotation.z = -t * 0.9;
      ringRef.current.rotation.x = Math.sin(t * 1.5) * 0.4;
    }

    if (outerGimbalRef.current) {
      outerGimbalRef.current.rotation.y = t * 0.5;
    }

    if (pointLightRef.current) {
      pointLightRef.current.intensity = 2.4 + Math.sin(t * 3.5) * 0.8;
    }
  });

  return (
    // Anchored at Room 101 cantilever on Floor 2: [-0.5, 0.45 + 0.55 = 1.0, 0.75]
    <group position={[0.1, 0.85, 0.75]}>
      {/* Structural mounting pin */}
      <mesh
        geometry={geometries.pedestalPin}
        material={materials.pinDark}
        position={[0, -0.1, 0]}
      />

      {/* Pulsing Emissive Core (AP-204 Incident Marker) */}
      <mesh
        ref={coreRef}
        geometry={geometries.core}
        material={materials.beaconEmissive}
        castShadow
      />

      {/* Inner Rotating Torus */}
      <mesh
        ref={ringRef}
        geometry={geometries.outerRing}
        material={materials.ringAccent}
      />

      {/* Outer Gimbal Ring */}
      <group ref={outerGimbalRef}>
        <mesh
          geometry={geometries.gimbalRing}
          material={materials.amberAlert}
        />
      </group>

      {/* Localized PointLight casting electric cyan onto Room 101 floor and walls */}
      <pointLight
        ref={pointLightRef}
        color="#00E5FF"
        intensity={2.6}
        distance={2.4}
        decay={2}
      />
    </group>
  );
}

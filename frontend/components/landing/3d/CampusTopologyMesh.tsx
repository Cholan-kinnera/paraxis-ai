"use client";

import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

interface CampusTopologyMeshProps {
  reducedMotion?: boolean;
}

export function CampusTopologyMesh({ reducedMotion = false }: CampusTopologyMeshProps) {
  const groupRef = useRef<THREE.Group>(null);
  const secondaryGroupRef = useRef<THREE.Group>(null);

  // Procedural geometries for architectural blocks and floor plates
  const geometries = useMemo(() => {
    return {
      mainTower: new THREE.BoxGeometry(1.6, 2.8, 1.4),
      floorPlate: new THREE.BoxGeometry(2.4, 0.06, 2.0),
      roomChamber: new THREE.BoxGeometry(0.9, 0.7, 0.8),
      adjacentWing: new THREE.BoxGeometry(1.2, 1.6, 1.8),
      tertiaryDistrict: new THREE.BoxGeometry(1.0, 1.1, 1.0),
      satelliteBlock: new THREE.BoxGeometry(0.7, 0.9, 0.7),
      columnTruss: new THREE.CylinderGeometry(0.025, 0.025, 2.2, 8),
      edgeBevel: new THREE.BoxGeometry(1.62, 0.02, 1.42),
    };
  }, []);

  // Frame materials
  const materials = useMemo(() => {
    return {
      architecturalDark: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#0A101D"),
        metalness: 0.85,
        roughness: 0.28,
      }),
      glassSlab: new THREE.MeshPhysicalMaterial({
        color: new THREE.Color("#0E1F38"),
        metalness: 0.2,
        roughness: 0.15,
        transmission: 0.6,
        thickness: 0.5,
        transparent: true,
        opacity: 0.8,
      }),
      hairlineEdge: new THREE.MeshBasicMaterial({
        color: new THREE.Color("#00E5FF"),
        wireframe: true,
        transparent: true,
        opacity: 0.18,
      }),
      subtleEdge: new THREE.MeshBasicMaterial({
        color: new THREE.Color("#6366F1"),
        wireframe: true,
        transparent: true,
        opacity: 0.12,
      }),
      accentPlate: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#030712"),
        metalness: 0.9,
        roughness: 0.2,
      }),
      beaconPedestal: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#062038"),
        emissive: new THREE.Color("#003852"),
        emissiveIntensity: 0.6,
        roughness: 0.3,
        metalness: 0.7,
      }),
    };
  }, []);

  // Subtle breathing idle drift (controlled & expensive, not a screensaver)
  useFrame((state) => {
    if (reducedMotion || !groupRef.current) return;
    const t = state.clock.getElapsedTime();
    groupRef.current.position.y = Math.sin(t * 0.6) * 0.08;
    groupRef.current.rotation.y = Math.sin(t * 0.2) * 0.04;

    if (secondaryGroupRef.current) {
      secondaryGroupRef.current.position.y = Math.cos(t * 0.5) * 0.05;
      secondaryGroupRef.current.rotation.y = -Math.sin(t * 0.15) * 0.03;
    }
  });

  return (
    <group ref={groupRef} position={[0.6, -0.2, 0]}>
      {/* 1. Primary Structural Block: Engineering Block (Central Core) */}
      <group position={[0, 0, 0]}>
        {/* Main Monolith Body */}
        <mesh
          geometry={geometries.mainTower}
          material={materials.architecturalDark}
          position={[0, 0.4, 0]}
          castShadow
          receiveShadow
        />
        {/* Architectural Wireframe Overlay */}
        <mesh
          geometry={geometries.mainTower}
          material={materials.hairlineEdge}
          position={[0, 0.4, 0]}
        />

        {/* Floor Plate 1 (Ground Mezzanine) */}
        <mesh
          geometry={geometries.floorPlate}
          material={materials.glassSlab}
          position={[0, -0.6, 0]}
          receiveShadow
        />

        {/* Floor Plate 2 (Target Incident Level - Floor 2) */}
        <mesh
          geometry={geometries.floorPlate}
          material={materials.glassSlab}
          position={[0, 0.4, 0]}
          receiveShadow
        />
        <mesh
          geometry={geometries.edgeBevel}
          material={materials.hairlineEdge}
          position={[0, 0.4, 0]}
        />

        {/* Floor Plate 3 (Upper Research Deck) */}
        <mesh
          geometry={geometries.floorPlate}
          material={materials.glassSlab}
          position={[0, 1.4, 0]}
          receiveShadow
        />

        {/* Cantilevered Hardware Systems Lab / Room 101 Spatial Chamber */}
        <mesh
          geometry={geometries.roomChamber}
          material={materials.beaconPedestal}
          position={[-0.5, 0.45, 0.75]}
          castShadow
          receiveShadow
        />
        <mesh
          geometry={geometries.roomChamber}
          material={materials.hairlineEdge}
          position={[-0.5, 0.45, 0.75]}
        />
      </group>

      {/* 2. Secondary Adjacent Wing: Computer Sciences & Systems Wing */}
      <group ref={secondaryGroupRef} position={[-1.8, -0.2, -0.8]}>
        <mesh
          geometry={geometries.adjacentWing}
          material={materials.architecturalDark}
          castShadow
          receiveShadow
        />
        <mesh
          geometry={geometries.adjacentWing}
          material={materials.subtleEdge}
        />
        <mesh
          geometry={geometries.floorPlate}
          material={materials.glassSlab}
          position={[0, 0.6, 0]}
          scale={[0.7, 1, 0.7]}
        />
      </group>

      {/* 3. Midground Tertiary District Modules (Depth Separation at Z = -2.5 to -3.5) */}
      <group position={[1.8, 0.1, -1.8]}>
        <mesh
          geometry={geometries.tertiaryDistrict}
          material={materials.architecturalDark}
          castShadow
          receiveShadow
        />
        <mesh
          geometry={geometries.tertiaryDistrict}
          material={materials.subtleEdge}
        />
      </group>

      <group position={[2.6, -0.4, 0.8]}>
        <mesh
          geometry={geometries.satelliteBlock}
          material={materials.architecturalDark}
          castShadow
          receiveShadow
        />
        <mesh
          geometry={geometries.satelliteBlock}
          material={materials.hairlineEdge}
        />
      </group>

      {/* 4. Structural Columns / Floor Plate Risers */}
      <mesh
        geometry={geometries.columnTruss}
        material={materials.accentPlate}
        position={[-1.0, 0.4, 0.8]}
      />
      <mesh
        geometry={geometries.columnTruss}
        material={materials.accentPlate}
        position={[1.0, 0.4, 0.8]}
      />
      <mesh
        geometry={geometries.columnTruss}
        material={materials.accentPlate}
        position={[-1.0, 0.4, -0.8]}
      />
      <mesh
        geometry={geometries.columnTruss}
        material={materials.accentPlate}
        position={[1.0, 0.4, -0.8]}
      />
    </group>
  );
}

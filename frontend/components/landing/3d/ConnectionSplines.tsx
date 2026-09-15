"use client";

import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

interface ConnectionSplinesProps {
  reducedMotion?: boolean;
}

export function ConnectionSplines({ reducedMotion = false }: ConnectionSplinesProps) {
  const packet1Ref = useRef<THREE.Mesh>(null);
  const packet2Ref = useRef<THREE.Mesh>(null);
  const packet3Ref = useRef<THREE.Mesh>(null);

  // 1. Define real 3D CatmullRomCurve3 paths
  // Primary Pathway: Student Signal -> Engineering Block -> Floor 2 -> Room 101 / AP-204
  const signalPath = useMemo(() => {
    const points = [
      new THREE.Vector3(2.4, -0.4, 1.6),   // Student Signal intake origin
      new THREE.Vector3(1.6, -0.1, 1.2),   // Perimeter ingress
      new THREE.Vector3(0.6, 0.2, 0.6),    // Engineering Block mezzanine entry
      new THREE.Vector3(0.1, 0.5, 0.4),    // Floor 2 riser junction
      new THREE.Vector3(0.1, 0.85, 0.75),  // AP-204 Incident Beacon at Room 101
    ];
    return new THREE.CatmullRomCurve3(points, false, "catmullrom", 0.3);
  }, []);

  // Secondary Pathway: AP-204 -> Dispatch conduit -> Network Operations Hub
  const dispatchPath = useMemo(() => {
    const points = [
      new THREE.Vector3(0.1, 0.85, 0.75),   // AP-204 Incident Beacon
      new THREE.Vector3(-0.4, 1.1, 0.4),    // Ceiling riser
      new THREE.Vector3(-1.0, 0.8, -0.2),   // Skybridge link
      new THREE.Vector3(-1.8, 0.3, -0.8),   // Network Operations service wing
    ];
    return new THREE.CatmullRomCurve3(points, false, "catmullrom", 0.4);
  }, []);

  // Tertiary Telemetry Loop: Ambient grid signal line
  const telemetryPath = useMemo(() => {
    const points = [
      new THREE.Vector3(-1.8, 0.3, -0.8),
      new THREE.Vector3(-0.8, -0.4, -1.6),
      new THREE.Vector3(1.2, -0.5, -1.8),
      new THREE.Vector3(2.4, -0.4, 1.6),
    ];
    return new THREE.CatmullRomCurve3(points, true, "catmullrom", 0.5);
  }, []);

  // Generate 3D Tube geometries
  const tubeGeometries = useMemo(() => {
    return {
      signalTube: new THREE.TubeGeometry(signalPath, 64, 0.014, 8, false),
      dispatchTube: new THREE.TubeGeometry(dispatchPath, 48, 0.012, 8, false),
      telemetryTube: new THREE.TubeGeometry(telemetryPath, 64, 0.008, 6, true),
      packetGeometry: new THREE.SphereGeometry(0.045, 12, 12),
      waypointGeometry: new THREE.OctahedronGeometry(0.06, 0),
    };
  }, [signalPath, dispatchPath, telemetryPath]);

  // Materials
  const materials = useMemo(() => {
    return {
      signalConduit: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#00E5FF"),
        emissive: new THREE.Color("#00B4D8"),
        emissiveIntensity: 1.8,
        roughness: 0.2,
        metalness: 0.4,
        transparent: true,
        opacity: 0.7,
      }),
      dispatchConduit: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#818CF8"),
        emissive: new THREE.Color("#4F46E5"),
        emissiveIntensity: 1.4,
        roughness: 0.2,
        metalness: 0.3,
        transparent: true,
        opacity: 0.55,
      }),
      ambientConduit: new THREE.MeshBasicMaterial({
        color: new THREE.Color("#1E293B"),
        wireframe: true,
        transparent: true,
        opacity: 0.25,
      }),
      emissivePacket: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#FFFFFF"),
        emissive: new THREE.Color("#00E5FF"),
        emissiveIntensity: 4.5,
        roughness: 0.1,
      }),
      dispatchPacket: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#F59E0B"),
        emissive: new THREE.Color("#F59E0B"),
        emissiveIntensity: 3.5,
        roughness: 0.1,
      }),
      originWaypoint: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#10B981"),
        emissive: new THREE.Color("#10B981"),
        emissiveIntensity: 2.0,
      }),
      endpointWaypoint: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#6366F1"),
        emissive: new THREE.Color("#6366F1"),
        emissiveIntensity: 2.0,
      }),
    };
  }, []);

  // Frame animation: Advance signal packets along splines
  useFrame((state) => {
    if (reducedMotion) return;
    const t = state.clock.getElapsedTime();

    // Packet 1: Student Signal -> AP-204 (speed: cycle every 3.2s)
    if (packet1Ref.current) {
      const u1 = (t * 0.35) % 1;
      const pos1 = signalPath.getPointAt(u1);
      packet1Ref.current.position.copy(pos1);
    }

    // Packet 2: Staggered second student report on same path
    if (packet2Ref.current) {
      const u2 = ((t * 0.35) + 0.5) % 1;
      const pos2 = signalPath.getPointAt(u2);
      packet2Ref.current.position.copy(pos2);
    }

    // Packet 3: Dispatch signal travelling to Network Operations
    if (packet3Ref.current) {
      const u3 = (t * 0.45) % 1;
      const pos3 = dispatchPath.getPointAt(u3);
      packet3Ref.current.position.copy(pos3);
    }
  });

  return (
    <group>
      {/* 3D Curved Conduits */}
      <mesh geometry={tubeGeometries.signalTube} material={materials.signalConduit} />
      <mesh geometry={tubeGeometries.dispatchTube} material={materials.dispatchConduit} />
      <mesh geometry={tubeGeometries.telemetryTube} material={materials.ambientConduit} />

      {/* Origin Node: Student Signal Intake Node */}
      <mesh
        geometry={tubeGeometries.waypointGeometry}
        material={materials.originWaypoint}
        position={[2.4, -0.4, 1.6]}
      />

      {/* Destination Node: Network Operations Service Unit */}
      <mesh
        geometry={tubeGeometries.waypointGeometry}
        material={materials.endpointWaypoint}
        position={[-1.8, 0.3, -0.8]}
      />

      {/* Animated Traveling Signal Packets */}
      <mesh
        ref={packet1Ref}
        geometry={tubeGeometries.packetGeometry}
        material={materials.emissivePacket}
      />
      <mesh
        ref={packet2Ref}
        geometry={tubeGeometries.packetGeometry}
        material={materials.emissivePacket}
      />
      <mesh
        ref={packet3Ref}
        geometry={tubeGeometries.packetGeometry}
        material={materials.dispatchPacket}
      />
    </group>
  );
}

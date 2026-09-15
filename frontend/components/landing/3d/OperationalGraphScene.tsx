"use client";

import React, { useRef, useMemo, useState } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

export interface GraphNodeData {
  id: string;
  type: "organization" | "campus" | "department" | "building" | "floor" | "room" | "asset" | "incident" | "task" | "team";
  name: string;
  sublabel: string;
  position: [number, number, number];
  status: "normal" | "affected" | "active-remediation";
  ancestry: string[];
}

interface OperationalGraphSceneProps {
  selectedNodeId?: string;
  onSelectNode: (nodeId: string) => void;
  reducedMotion?: boolean;
}

export const GRAPH_SPATIAL_NODES: GraphNodeData[] = [
  {
    id: "org",
    type: "organization",
    name: "Paraxis Demo Campus",
    sublabel: "Institutional Tenant Root",
    position: [0, -1.6, 0],
    status: "normal",
    ancestry: ["org"],
  },
  {
    id: "campus",
    type: "campus",
    name: "Engineering Campus",
    sublabel: "Active Operational Zone",
    position: [0, -0.85, 0],
    status: "normal",
    ancestry: ["org", "campus"],
  },
  {
    id: "dept",
    type: "department",
    name: "Network Operations",
    sublabel: "Owning Service Unit",
    position: [-2.2, 0.2, -0.6],
    status: "active-remediation",
    ancestry: ["org", "campus", "dept"],
  },
  {
    id: "bldg",
    type: "building",
    name: "Engineering Block",
    sublabel: "Facility Structure",
    position: [0.8, 0.1, 0.2],
    status: "affected",
    ancestry: ["org", "campus", "bldg"],
  },
  {
    id: "fl",
    type: "floor",
    name: "Floor 2",
    sublabel: "Spatial Level",
    position: [0.8, 0.8, 0.2],
    status: "affected",
    ancestry: ["org", "campus", "bldg", "fl"],
  },
  {
    id: "rm",
    type: "room",
    name: "Room 101",
    sublabel: "Hardware Systems Lab",
    position: [0.3, 1.25, 0.7],
    status: "affected",
    ancestry: ["org", "campus", "bldg", "fl", "rm"],
  },
  {
    id: "ast",
    type: "asset",
    name: "Network Access Point AP-204",
    sublabel: "PoE Uplink Hardware Node",
    position: [0.3, 1.7, 0.7],
    status: "active-remediation",
    ancestry: ["org", "campus", "bldg", "fl", "rm", "ast"],
  },
  {
    id: "inc",
    type: "incident",
    name: "Wi-Fi Connectivity Issue",
    sublabel: "7 Clustered Student Signals",
    position: [0.3, 2.15, 0.7],
    status: "active-remediation",
    ancestry: ["org", "campus", "bldg", "fl", "rm", "ast", "inc"],
  },
  {
    id: "task",
    type: "task",
    name: "Remediation Task",
    sublabel: "AP-204 Verification & Reset",
    position: [-0.9, 1.4, 0.0],
    status: "active-remediation",
    ancestry: ["org", "campus", "bldg", "fl", "rm", "ast", "inc", "task"],
  },
  {
    id: "team",
    type: "team",
    name: "Network Specialist On-Site",
    sublabel: "Technician Dispatched",
    position: [-2.2, 0.8, -0.6],
    status: "active-remediation",
    ancestry: ["org", "campus", "dept", "team"],
  },
];

export function OperationalGraphScene({
  selectedNodeId = "ast",
  onSelectNode,
  reducedMotion = false,
}: OperationalGraphSceneProps) {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const orbitControlsRef = useRef<any>(null);

  // Selected node and ancestry list
  const selectedNode = GRAPH_SPATIAL_NODES.find((n) => n.id === selectedNodeId) || GRAPH_SPATIAL_NODES[6];
  const activeAncestry = useMemo(() => new Set(selectedNode.ancestry), [selectedNode]);

  // Procedural geometries mapped to entity semantics (NOT all spheres!)
  const nodeGeometries = useMemo(() => {
    return {
      organization: new THREE.CylinderGeometry(2.0, 2.2, 0.25, 32),
      campus: new THREE.CylinderGeometry(1.5, 1.6, 0.2, 32),
      department: new THREE.BoxGeometry(0.8, 0.6, 0.8),
      building: new THREE.BoxGeometry(1.0, 1.2, 1.0),
      floor: new THREE.BoxGeometry(1.4, 0.08, 1.4),
      room: new THREE.BoxGeometry(0.55, 0.45, 0.55),
      asset: new THREE.OctahedronGeometry(0.16, 0),
      incident: new THREE.IcosahedronGeometry(0.18, 0),
      task: new THREE.BoxGeometry(0.24, 0.24, 0.24),
      team: new THREE.ConeGeometry(0.2, 0.35, 16),
      pulsePacket: new THREE.SphereGeometry(0.04, 12, 12),
    };
  }, []);

  // Shared connection paths
  const connectionPaths = useMemo(() => {
    const getNodePos = (id: string) => {
      const n = GRAPH_SPATIAL_NODES.find((x) => x.id === id);
      return n ? new THREE.Vector3(...n.position) : new THREE.Vector3();
    };

    const links: { from: string; to: string; active: boolean; curve: THREE.CatmullRomCurve3 }[] = [
      { from: "org", to: "campus", active: false, curve: new THREE.CatmullRomCurve3([getNodePos("org"), getNodePos("campus")]) },
      { from: "campus", to: "bldg", active: false, curve: new THREE.CatmullRomCurve3([getNodePos("campus"), getNodePos("bldg")]) },
      { from: "campus", to: "dept", active: false, curve: new THREE.CatmullRomCurve3([getNodePos("campus"), getNodePos("dept")]) },
      { from: "bldg", to: "fl", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("bldg"), getNodePos("fl")]) },
      { from: "fl", to: "rm", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("fl"), getNodePos("rm")]) },
      { from: "rm", to: "ast", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("rm"), getNodePos("ast")]) },
      { from: "ast", to: "inc", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("ast"), getNodePos("inc")]) },
      { from: "inc", to: "task", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("inc"), getNodePos("task")]) },
      { from: "task", to: "team", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("task"), getNodePos("team")]) },
      { from: "team", to: "dept", active: true, curve: new THREE.CatmullRomCurve3([getNodePos("team"), getNodePos("dept")]) },
    ];

    return links.map((l) => ({
      ...l,
      geom: new THREE.TubeGeometry(l.curve, 24, l.active ? 0.016 : 0.009, 8, false),
    }));
  }, []);

  // Materials
  const materials = useMemo(() => {
    return {
      activeHighlight: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#00E5FF"),
        emissive: new THREE.Color("#00E5FF"),
        emissiveIntensity: 2.5,
        roughness: 0.1,
      }),
      normalArchitectural: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#0B132B"),
        metalness: 0.85,
        roughness: 0.25,
      }),
      affectedMaterial: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#0A2540"),
        emissive: new THREE.Color("#00527A"),
        emissiveIntensity: 1.2,
        roughness: 0.2,
      }),
      incidentAlert: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#EF4444"),
        emissive: new THREE.Color("#EF4444"),
        emissiveIntensity: 3.0,
        roughness: 0.1,
      }),
      wireframeAccent: new THREE.MeshBasicMaterial({
        color: new THREE.Color("#00E5FF"),
        wireframe: true,
        transparent: true,
        opacity: 0.25,
      }),
      activeTube: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#00E5FF"),
        emissive: new THREE.Color("#00B4D8"),
        emissiveIntensity: 2.0,
        roughness: 0.2,
        transparent: true,
        opacity: 0.85,
      }),
      dormantTube: new THREE.MeshBasicMaterial({
        color: new THREE.Color("#1E293B"),
        transparent: true,
        opacity: 0.3,
      }),
      emissivePacket: new THREE.MeshStandardMaterial({
        color: new THREE.Color("#FFFFFF"),
        emissive: new THREE.Color("#00E5FF"),
        emissiveIntensity: 4.0,
      }),
    };
  }, []);

  // Animated packet ref along the active traversal link
  const packetRef = useRef<THREE.Mesh>(null);
  const activeChainCurve = useMemo(() => {
    return new THREE.CatmullRomCurve3(
      [
        new THREE.Vector3(0.8, 0.8, 0.2),    // Floor 2
        new THREE.Vector3(0.3, 1.25, 0.7),   // Room 101
        new THREE.Vector3(0.3, 1.7, 0.7),    // AP-204
        new THREE.Vector3(0.3, 2.15, 0.7),   // Incident
        new THREE.Vector3(-0.9, 1.4, 0.0),   // Task
        new THREE.Vector3(-2.2, 0.8, -0.6),  // Team
      ],
      false,
      "catmullrom",
      0.3
    );
  }, []);

  useFrame((state) => {
    if (reducedMotion) return;
    const t = state.clock.getElapsedTime();

    if (packetRef.current) {
      const u = (t * 0.28) % 1;
      const pt = activeChainCurve.getPointAt(u);
      packetRef.current.position.copy(pt);
    }
  });

  return (
    <>
      {/* Lighting Rig */}
      <ambientLight color="#070C1B" intensity={1.5} />
      <directionalLight position={[5, 8, 5]} color="#00E5FF" intensity={2.5} />
      <directionalLight position={[-6, 4, -4]} color="#6366F1" intensity={2.0} />
      <pointLight position={[0.3, 1.8, 0.7]} color="#00E5FF" intensity={3.0} distance={3.5} />

      {/* OrbitControls for user exploration (restricted pitch & zoom) */}
      <OrbitControls
        ref={orbitControlsRef}
        enablePan={false}
        enableZoom={true}
        minDistance={3.5}
        maxDistance={9.0}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2.1}
        dampingFactor={0.05}
        autoRotate={!reducedMotion}
        autoRotateSpeed={0.4}
      />

      {/* Connection Tubes */}
      {connectionPaths.map((link, idx) => {
        const isChainActive = activeAncestry.has(link.from) && activeAncestry.has(link.to);
        return (
          <mesh
            key={`link-${idx}`}
            geometry={link.geom}
            material={isChainActive ? materials.activeTube : materials.dormantTube}
          />
        );
      })}

      {/* Animated Traveling Signal Packet */}
      <mesh
        ref={packetRef}
        geometry={nodeGeometries.pulsePacket}
        material={materials.emissivePacket}
      />

      {/* Hierarchy Nodes */}
      {GRAPH_SPATIAL_NODES.map((node) => {
        const isSelected = selectedNodeId === node.id;
        const isHovered = hoveredNodeId === node.id;
        const isInAncestry = activeAncestry.has(node.id);

        let mat = materials.normalArchitectural;
        if (node.id === "inc") {
          mat = materials.incidentAlert;
        } else if (isSelected || isHovered) {
          mat = materials.activeHighlight;
        } else if (isInAncestry) {
          mat = materials.affectedMaterial;
        }

        const scaleMultiplier = isSelected ? 1.22 : isHovered ? 1.12 : 1.0;

        return (
          <group
            key={node.id}
            position={node.position}
            scale={[scaleMultiplier, scaleMultiplier, scaleMultiplier]}
            onPointerOver={(e) => {
              e.stopPropagation();
              setHoveredNodeId(node.id);
            }}
            onPointerOut={() => setHoveredNodeId(null)}
            onClick={(e) => {
              e.stopPropagation();
              onSelectNode(node.id);
            }}
          >
            <mesh
              geometry={nodeGeometries[node.type] as THREE.BufferGeometry}
              material={mat}
              castShadow
              receiveShadow
            />
            {/* Wireframe border highlight */}
            {(isSelected || isHovered || isInAncestry) && (
              <mesh
                geometry={nodeGeometries[node.type] as THREE.BufferGeometry}
                material={materials.wireframeAccent}
                scale={[1.05, 1.05, 1.05]}
              />
            )}
          </group>
        );
      })}
    </>
  );
}

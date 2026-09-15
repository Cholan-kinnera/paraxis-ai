import * as THREE from "three";

/**
 * Procedural material palettes and custom PBR shaders for Paraxis AI 3D environments.
 * Strictly adheres to the obsidian, electric cyan (#00E5FF), cobalt (#6366F1), and emerald (#10B981) palette.
 */

// Premium dark architectural metallic surface for campus building blocks
export const architecturalMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#080E1A"),
  metalness: 0.88,
  roughness: 0.22,
  flatShading: false,
});

// Translucent frosted glass floor plate material
export const glassPlateMaterial = new THREE.MeshPhysicalMaterial({
  color: new THREE.Color("#0C192E"),
  metalness: 0.15,
  roughness: 0.18,
  transmission: 0.55,
  thickness: 0.6,
  transparent: true,
  opacity: 0.85,
  reflectivity: 0.8,
});

// Emissive cyan incident beacon material
export const incidentBeaconMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#00E5FF"),
  emissive: new THREE.Color("#00E5FF"),
  emissiveIntensity: 2.8,
  roughness: 0.1,
  metalness: 0.2,
});

// Glowing signal conduit material
export const signalConduitMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#00E5FF"),
  emissive: new THREE.Color("#00B4D8"),
  emissiveIntensity: 1.6,
  roughness: 0.2,
  metalness: 0.1,
  transparent: true,
  opacity: 0.85,
});

// Deep cobalt ambient architectural frame material
export const architecturalFrameMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#1E1B4B"),
  metalness: 0.9,
  roughness: 0.35,
  wireframe: false,
});

// Operational health emerald node material
export const operationalHealthMaterial = new THREE.MeshStandardMaterial({
  color: new THREE.Color("#10B981"),
  emissive: new THREE.Color("#10B981"),
  emissiveIntensity: 2.2,
  roughness: 0.15,
  metalness: 0.2,
});

// Hairline wireframe accent material
export const hairlineWireframeMaterial = new THREE.LineBasicMaterial({
  color: new THREE.Color("#00E5FF"),
  transparent: true,
  opacity: 0.25,
  linewidth: 1,
});

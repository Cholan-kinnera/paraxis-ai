"use client";
import { Canvas } from "@react-three/fiber";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import { DashSphere } from "./DashSphere";
import { useSceneStage } from "./stage";

export default function SceneCanvas({ color }: { color?: string }) {
  const stage = useSceneStage();
  return (
    <div className="fixed inset-0 z-0 bg-black pointer-events-none" aria-hidden>
      <Canvas dpr={[1, 1.75]} camera={{ position: [0, 0, 24], fov: 30 }} gl={{ antialias: false, powerPreference: "high-performance" }}>
        <DashSphere stage={stage} color={color} />
        <EffectComposer>
          <Bloom luminanceThreshold={0.3} luminanceSmoothing={0.5} intensity={1.25} mipmapBlur radius={0.55} />
        </EffectComposer>
      </Canvas>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_45%,rgba(0,0,0,0.85)_100%)]" />
    </div>
  );
}

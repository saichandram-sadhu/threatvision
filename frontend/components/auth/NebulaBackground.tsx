"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Stars } from "@react-three/drei";
import { useReducedMotion } from "framer-motion";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { AuthGradientFallback } from "./AuthGradientFallback";
import { ThreatVisionLogo3D } from "./ThreatVisionLogo3D";

function VioletMist({ reduced }: { reduced: boolean }) {
  const ref = useRef<THREE.Points>(null);
  const count = 900;
  const geometry = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const r = 6 + Math.random() * 18;
      const u = Math.random();
      const v = Math.random();
      const theta = 2 * Math.PI * u;
      const phi = Math.acos(2 * v - 1);
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.65;
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return g;
  }, [count]);

  useFrame((state) => {
    if (reduced || !ref.current) return;
    ref.current.rotation.y = state.clock.elapsedTime * 0.018;
  });

  return (
    <points ref={ref} geometry={geometry}>
      <pointsMaterial
        size={0.07}
        color="#c084fc"
        transparent
        opacity={0.35}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

function NebulaScene({ reduced }: { reduced: boolean }) {
  return (
    <>
      <color attach="background" args={["#050508"]} />
      <ambientLight intensity={0.22} />
      <pointLight position={[12, 8, 10]} intensity={1.1} color="#22d3ee" />
      <pointLight position={[-10, -4, 6]} intensity={0.65} color="#a78bfa" />
      <Stars
        radius={90}
        depth={70}
        count={2800}
        factor={3.2}
        saturation={0.12}
        fade
        speed={reduced ? 0 : 0.22}
      />
      <VioletMist reduced={reduced} />
      <ThreatVisionLogo3D reducedMotion={reduced} />
    </>
  );
}

export function NebulaBackground() {
  const reduced = useReducedMotion() ?? false;

  if (reduced) {
    return <AuthGradientFallback />;
  }

  return (
    <div
      className="pointer-events-none absolute inset-0 z-0"
      aria-hidden
    >
      <Canvas
        camera={{ position: [0, 0.2, 14], fov: 42 }}
        dpr={[1, 2]}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        }}
        style={{ width: "100%", height: "100%" }}
      >
        <NebulaScene reduced={false} />
      </Canvas>
    </div>
  );
}

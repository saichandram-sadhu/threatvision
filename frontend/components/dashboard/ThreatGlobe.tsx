"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useMemo } from "react";
import * as THREE from "three";

import { hashIpToLatLng } from "@/lib/geo/hashIpToGlobe";
import type { TopIpRow } from "@/lib/types/dashboard";

function latLngToVec3(lat: number, lng: number, r: number): THREE.Vector3 {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lng + 180) * Math.PI) / 180;
  return new THREE.Vector3(
    -(r * Math.sin(phi) * Math.cos(theta)),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  );
}

function GlobeMarkers({ topIps }: { topIps: TopIpRow[] }) {
  const { positions, scales } = useMemo(() => {
    const slice = topIps.slice(0, 16);
    const max = Math.max(1, ...slice.map((t) => t.count));
    const positions: THREE.Vector3[] = [];
    const scales: number[] = [];
    const r = 1.03;
    for (const row of slice) {
      const { lat, lng } = hashIpToLatLng(row.ip);
      positions.push(latLngToVec3(lat, lng, r));
      scales.push(0.014 + (row.count / max) * 0.018);
    }
    return { positions, scales };
  }, [topIps]);

  return (
    <group>
      <mesh>
        <sphereGeometry args={[1, 56, 56]} />
        <meshStandardMaterial
          color="#0a0d14"
          emissive="#132038"
          emissiveIntensity={0.45}
          metalness={0.35}
          roughness={0.55}
        />
      </mesh>
      <mesh>
        <sphereGeometry args={[1.002, 32, 32]} />
        <meshBasicMaterial color="#22d3ee" wireframe transparent opacity={0.12} depthWrite={false} />
      </mesh>
      {positions.map((p, i) => (
        <mesh key={i} position={p}>
          <sphereGeometry args={[scales[i] ?? 0.02, 10, 10]} />
          <meshBasicMaterial color="#ff2d55" />
        </mesh>
      ))}
      <ambientLight intensity={0.35} />
      <pointLight position={[6, 4, 8]} intensity={1.4} color="#22d3ee" />
      <pointLight position={[-5, -2, -4]} intensity={0.5} color="#a78bfa" />
      <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.35} />
    </group>
  );
}

export function ThreatGlobe({ topIps }: { topIps: TopIpRow[] }) {
  const empty = topIps.length === 0;

  return (
    <div className="dash-section relative h-[min(22rem,50vw)] w-full overflow-hidden rounded-xl border border-white/[0.08] bg-tv-void ring-1 ring-white/[0.05]">
      <Canvas
        camera={{ position: [0, 0.35, 2.85], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        className="h-full w-full"
      >
        <color attach="background" args={["transparent"]} />
        {empty ? (
          <group>
            <mesh>
              <sphereGeometry args={[1, 48, 48]} />
              <meshStandardMaterial
                color="#080a10"
                emissive="#1a2030"
                emissiveIntensity={0.3}
                metalness={0.25}
                roughness={0.65}
              />
            </mesh>
            <ambientLight intensity={0.4} />
            <pointLight position={[4, 2, 6]} intensity={0.9} color="#22d3ee" />
            <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.25} />
          </group>
        ) : (
          <GlobeMarkers topIps={topIps} />
        )}
      </Canvas>
      {empty && (
        <p className="pointer-events-none absolute bottom-3 left-0 right-0 text-center text-xs text-tv-muted">
          Analyze IPv4 IOCs to plot pseudo-positions on the globe (visualization only).
        </p>
      )}
    </div>
  );
}

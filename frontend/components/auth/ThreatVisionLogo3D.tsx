"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

type Props = {
  /** When true, shield stays fixed (caller should set from prefers-reduced-motion). */
  reducedMotion?: boolean;
};

function buildShieldShape() {
  const w = 0.92;
  const s = new THREE.Shape();
  s.moveTo(0, 1.28);
  s.lineTo(w, 0.98);
  s.lineTo(w, 0.12);
  s.quadraticCurveTo(w * 0.88, -0.68, 0, -1.18);
  s.quadraticCurveTo(-w * 0.88, -0.68, -w, 0.12);
  s.lineTo(-w, 0.98);
  s.lineTo(0, 1.28);
  return s;
}

export function ThreatVisionLogo3D({ reducedMotion }: Props) {
  const group = useRef<THREE.Group>(null);

  const geometry = useMemo(() => {
    const shape = buildShieldShape();
    return new THREE.ExtrudeGeometry(shape, {
      depth: 0.22,
      bevelEnabled: true,
      bevelThickness: 0.05,
      bevelSize: 0.045,
      bevelSegments: 2,
      curveSegments: 12,
    });
  }, []);

  useFrame((state, dt) => {
    if (reducedMotion || !group.current) return;
    group.current.rotation.y += dt * 0.42;
    const wobble = Math.sin(state.clock.elapsedTime * 0.55) * 0.08;
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, wobble, 0.04);
  });

  return (
    <group ref={group} position={[0, -0.15, 0]} scale={1.75}>
      <mesh geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial
          color="#0a0c12"
          metalness={0.88}
          roughness={0.22}
          emissive="#22d3ee"
          emissiveIntensity={0.42}
        />
      </mesh>
    </group>
  );
}

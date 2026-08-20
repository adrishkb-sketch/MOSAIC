"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Float, MeshTransmissionMaterial, Environment, Sphere } from "@react-three/drei";
import * as THREE from "three";
import { useTheme } from "next-themes";

function QuantumCore({ isLight }: { isLight: boolean }) {
  const outerRef = useRef<THREE.Mesh>(null);
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);
  const ring3Ref = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.x += delta * 0.2;
      outerRef.current.rotation.y += delta * 0.3;
    }
    if (ring1Ref.current) {
      ring1Ref.current.rotation.x += delta * 0.5;
      ring1Ref.current.rotation.y += delta * 0.1;
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.y -= delta * 0.4;
      ring2Ref.current.rotation.z += delta * 0.2;
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.x -= delta * 0.3;
      ring3Ref.current.rotation.z -= delta * 0.5;
    }
  });

  const coreGlow = isLight ? "#4f46e5" : "#a855f7"; // Indigo/Purple
  const ringColor = isLight ? "#6366f1" : "#c084fc";
  const glassColor = isLight ? "#ffffff" : "#e0e7ff";

  return (
    <group>
      {/* Intense Inner Core representing the AI brain */}
      <Sphere args={[0.4, 32, 32]}>
        <meshBasicMaterial color={coreGlow} />
        <pointLight color={coreGlow} intensity={isLight ? 2 : 4} distance={10} />
      </Sphere>

      {/* Refractive Glass Shell representing the outer interface */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1.2, 1]} />
        <MeshTransmissionMaterial
          backside={true}
          samples={4}
          thickness={0.5}
          chromaticAberration={0.05}
          anisotropy={0.1}
          distortion={0.2}
          distortionScale={0.3}
          temporalDistortion={0.1}
          color={glassColor}
          transmission={1}
          roughness={0.1}
        />
      </mesh>

      {/* Data Rings representing information flow */}
      <mesh ref={ring1Ref}>
        <torusGeometry args={[1.6, 0.02, 16, 100]} />
        <meshStandardMaterial color={ringColor} emissive={ringColor} emissiveIntensity={1} />
      </mesh>
      
      <mesh ref={ring2Ref} rotation={[Math.PI / 3, 0, 0]}>
        <torusGeometry args={[1.8, 0.015, 16, 100]} />
        <meshStandardMaterial color={ringColor} emissive={ringColor} emissiveIntensity={0.5} />
      </mesh>

      <mesh ref={ring3Ref} rotation={[0, Math.PI / 4, Math.PI / 4]}>
        <torusGeometry args={[2.0, 0.01, 16, 100]} />
        <meshStandardMaterial color={ringColor} emissive={ringColor} emissiveIntensity={1.5} />
      </mesh>
    </group>
  );
}

export default function MosaicCore3D() {
  const { theme } = useTheme();
  const isLight = theme === "light";

  return (
    <div className="w-full h-full min-h-[300px]">
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }} gl={{ antialias: true }}>
        <ambientLight intensity={isLight ? 2 : 0.5} />
        <Environment preset={isLight ? "studio" : "city"} />
        
        <Float speed={2.5} rotationIntensity={0.5} floatIntensity={1.5}>
          <QuantumCore isLight={isLight} />
        </Float>
        
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          autoRotate 
          autoRotateSpeed={1.0} 
        />
      </Canvas>
    </div>
  );
}

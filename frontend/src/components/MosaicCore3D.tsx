"use client";

import React, { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Sphere, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

function CoreGeometry() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.2;
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.3;
    }
  });

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1.5, 0]} />
      <meshStandardMaterial
        color="#8b5cf6"
        wireframe={true}
        emissive="#4f46e5"
        emissiveIntensity={1.5}
      />
    </mesh>
  );
}

function InnerCore() {
  return (
    <Sphere args={[1, 64, 64]}>
      <MeshDistortMaterial
        color="#a855f7"
        attach="material"
        distort={0.4}
        speed={2}
        roughness={0}
      />
    </Sphere>
  );
}

export default function MosaicCore3D() {
  return (
    <div className="w-full h-full min-h-[300px]">
      <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[2, 2, 5]} intensity={1.5} />
        <pointLight position={[-2, -2, -2]} intensity={1} color="#4f46e5" />
        
        <CoreGeometry />
        <InnerCore />
        
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate={true}
          autoRotateSpeed={1.5}
        />
      </Canvas>
    </div>
  );
}

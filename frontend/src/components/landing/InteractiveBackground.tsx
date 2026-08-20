"use client";

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

// Fallback random generator if maath isn't installed
function generateParticles(count: number, radius: number) {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const r = radius * Math.cbrt(Math.random());
    const theta = Math.random() * 2 * Math.PI;
    const phi = Math.acos(2 * Math.random() - 1);
    
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
  }
  return positions;
}

import { useTheme } from "next-themes";

interface InteractiveBackgroundProps {
  status?: "idle" | "browsing" | "error";
}

function ParticleSwarm({ status = "idle", theme, ...props }: { status: string, theme?: string } & React.ComponentPropsWithoutRef<typeof Points>) {
  const ref = useRef<THREE.Points>(null);
  const materialRef = useRef<THREE.PointsMaterial>(null);
  
  const sphere = useMemo(() => {
    return generateParticles(5000, 1.5);
  }, []);

  const targetColor = useMemo(() => new THREE.Color(), []);

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta / 10;
      ref.current.rotation.y -= delta / 15;
    }
    
    if (materialRef.current) {
      // Determine target color based on status and theme
      const isLight = theme === "light";
      let hexColor = isLight ? "#4338ca" : "#8b5cf6"; // idle (indigo-700 light, violet-500 dark)
      if (status === "browsing") hexColor = isLight ? "#047857" : "#10b981"; // browsing (emerald-700 light, emerald-500 dark)
      else if (status === "error") hexColor = isLight ? "#be123c" : "#f43f5e"; // error (rose-700 light, rose-500 dark)
      
      targetColor.set(hexColor);
      materialRef.current.color.lerp(targetColor, 0.05);
    }
  });

  const isLight = theme === "light";

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false} {...props}>
        <PointMaterial
          ref={materialRef}
          transparent
          color={isLight ? "#4338ca" : "#8b5cf6"}
          size={isLight ? 0.007 : 0.005}
          sizeAttenuation={true}
          depthWrite={false}
          blending={isLight ? THREE.NormalBlending : THREE.AdditiveBlending}
          opacity={isLight ? 0.8 : 1}
        />
      </Points>
    </group>
  );
}

export default function InteractiveBackground({ status = "idle" }: InteractiveBackgroundProps) {
  const { theme } = useTheme();
  
  return (
    <div className="absolute inset-0 w-full h-full opacity-60 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 1] }}>
        <ParticleSwarm status={status} theme={theme} />
      </Canvas>
    </div>
  );
}

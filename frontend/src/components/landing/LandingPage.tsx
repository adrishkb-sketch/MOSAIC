"use client";

import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import InteractiveBackground from './InteractiveBackground';
import HeroSection from './HeroSection';
import HowItWorksSection from './HowItWorksSection';
import FeaturesSection from './FeaturesSection';
import ProductPreviewSection from './ProductPreviewSection';
import TechnologySection from './TechnologySection';
import Footer from './Footer';
import LoginSplash from '../LoginSplash';
import { ThemeToggle } from '../ThemeToggle';

interface LandingPageProps {
  onLogin: (email: string) => void;
}

export default function LandingPage({ onLogin }: LandingPageProps) {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <div className="relative min-h-screen bg-transparent text-slate-900 dark:text-slate-100 overflow-x-hidden selection:bg-indigo-500/30 font-sans">
      <InteractiveBackground />
      <div className="absolute top-6 right-6 z-40">
        <ThemeToggle />
      </div>

      <main>
        <HeroSection onGetStarted={() => setShowLogin(true)} />
        <HowItWorksSection />
        <FeaturesSection />
        <ProductPreviewSection />
        <TechnologySection />
      </main>

      <Footer />

      {/* Login Modal Overlay */}
      <AnimatePresence>
        {showLogin && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 dark:bg-black/40 backdrop-blur-md"
          >
            <button 
              onClick={() => setShowLogin(false)}
              className="absolute top-8 right-8 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:text-white transition-colors text-sm font-medium z-50"
            >
              Close [ESC]
            </button>
            <div className="w-full h-full flex items-center justify-center overflow-y-auto">
              <LoginSplash onLogin={onLogin} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

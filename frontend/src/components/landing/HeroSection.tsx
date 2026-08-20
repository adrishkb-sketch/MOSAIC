import React from 'react';
import { motion } from 'framer-motion';
import { Rocket, Sparkles } from 'lucide-react';

interface HeroSectionProps {
  onGetStarted: () => void;
}

export default function HeroSection({ onGetStarted }: HeroSectionProps) {
  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20 pb-32 px-6">
      <div className="max-w-5xl mx-auto text-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm font-medium mb-8"
        >
          <Sparkles size={16} />
          <span>The Next Generation Web Agent</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 font-display"
        >
          Browse the web with <br className="hidden md:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            Superhuman Intelligence
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          MOSAIC learns the web, not your identity. Experience a universal personal browser agent that automates tasks, extracts data, and navigates seamlessly—all within an isolated, privacy-first environment.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <button
            onClick={onGetStarted}
            className="group relative px-8 py-4 w-full sm:w-auto rounded-xl bg-slate-100 text-slate-900 font-bold text-lg hover:bg-white transition-all overflow-hidden flex items-center justify-center gap-2"
          >
            <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 group-hover:opacity-100 opacity-0 transition-opacity" />
            <span>Get Started Free</span>
            <Rocket size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
          
          <a
            href="#how-it-works"
            className="px-8 py-4 w-full sm:w-auto rounded-xl bg-slate-100 dark:bg-slate-900/50 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-slate-900 dark:text-white font-medium hover:bg-slate-200 dark:bg-slate-800 transition-all text-center"
          >
            Learn How It Works
          </a>
        </motion.div>
      </div>

      {/* Hero ambient glows */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
    </section>
  );
}

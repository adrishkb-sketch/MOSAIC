import React from 'react';
import { motion } from 'framer-motion';

export default function ProductPreviewSection() {
  return (
    <section className="py-32 px-6 relative z-10">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold mb-6 font-display">Experience the Interface</h2>
          <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto text-lg">
            A sleek, command-driven dashboard designed for maximum efficiency.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="relative mx-auto max-w-5xl rounded-2xl border border-slate-300/50 dark:border-white/10 glass-panel overflow-hidden shadow-2xl"
        >
          {/* Mockup Top Bar */}
          <div className="bg-slate-100 dark:bg-slate-900/80 px-4 py-3 flex items-center gap-2 border-b border-slate-300/30 dark:border-white/5">
            <div className="w-3 h-3 rounded-full bg-rose-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <div className="ml-4 text-xs font-mono text-slate-500">mosaic-os-session</div>
          </div>
          
          {/* Mockup Body */}
          <div className="h-[500px] bg-slate-50 dark:bg-slate-950/80 flex">
            {/* Sidebar Mock */}
            <div className="w-64 border-r border-slate-300/30 dark:border-white/5 p-4 hidden md:block">
              <div className="h-8 bg-slate-200/50 dark:bg-white/5 rounded-lg mb-6" />
              <div className="space-y-3">
                <div className="h-4 w-3/4 bg-slate-200/50 dark:bg-white/5 rounded" />
                <div className="h-4 w-1/2 bg-slate-200/50 dark:bg-white/5 rounded" />
                <div className="h-4 w-5/6 bg-slate-200/50 dark:bg-white/5 rounded" />
              </div>
            </div>
            {/* Main Area Mock */}
            <div className="flex-1 p-6 flex flex-col justify-end">
              <div className="space-y-4 mb-8">
                <div className="bg-indigo-500/20 text-indigo-200 p-4 rounded-2xl rounded-tl-sm w-3/4 self-start border border-indigo-500/10">
                  <div className="h-4 w-1/4 bg-indigo-400/20 rounded mb-2" />
                  <div className="h-4 w-5/6 bg-indigo-400/20 rounded" />
                </div>
                <div className="bg-slate-200 dark:bg-slate-800/50 p-4 rounded-2xl rounded-tr-sm w-1/2 ml-auto border border-slate-300/30 dark:border-white/5">
                  <div className="h-4 w-full bg-slate-200/50 dark:bg-white/5 rounded" />
                </div>
              </div>
              <div className="h-12 bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-300/50 dark:border-white/10 flex items-center px-4 mt-auto">
                <div className="h-4 w-1/3 bg-slate-300/50 dark:bg-white/10 rounded" />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

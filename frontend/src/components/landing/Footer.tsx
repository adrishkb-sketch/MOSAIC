import React from 'react';
import { Sparkles } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-slate-300/30 dark:border-white/5 py-12 px-6 relative z-10 bg-slate-50 dark:bg-slate-950">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-500" />
          <span className="text-lg font-bold font-display tracking-tight text-slate-200">MOSAIC</span>
        </div>
        
        <p className="text-slate-500 text-sm text-center md:text-left">
          © {new Date().getFullYear()} MOSAIC OS. All rights reserved.
        </p>

        <div className="flex gap-6">
          <a href="#" className="text-sm text-slate-500 hover:text-indigo-400 transition-colors">Privacy</a>
          <a href="#" className="text-sm text-slate-500 hover:text-indigo-400 transition-colors">Terms</a>
          <a href="#" className="text-sm text-slate-500 hover:text-indigo-400 transition-colors">GitHub</a>
        </div>
      </div>
    </footer>
  );
}

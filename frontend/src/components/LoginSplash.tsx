"use client";

import React, { useState } from "react";
import { Sparkles, Shield, AlertTriangle, Rocket, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import MosaicCore3D from "./MosaicCore3D";

interface LoginSplashProps {
  onLogin: (email: string) => void;
}

export default function LoginSplash({ onLogin }: LoginSplashProps) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email) {
      setError("Email is required");
      return;
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      onLogin(email);
    }, 800);
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row items-center justify-center p-6 bg-transparent relative overflow-hidden h-screen gap-12">
      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl animate-pulse" />

      {/* 3D Core Element */}
      <motion.div 
        className="w-full lg:w-1/2 h-[40vh] lg:h-[80vh] relative z-10 flex items-center justify-center"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1 }}
      >
        <MosaicCore3D />
      </motion.div>

      <motion.div 
        className="w-full max-w-md p-8 rounded-3xl glass-panel relative z-10 transition-all hover:border-white/20 hover:shadow-indigo-500/10"
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <div className="flex flex-col items-center mb-8">
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
            <Sparkles size={28} className="text-indigo-400" /> MOSAIC OS
          </h1>
          <p className="text-sm text-indigo-200/70 mt-2 text-center font-medium flex items-center justify-center gap-1.5">
            MOSAIC learns the web, not your identity. <Shield size={14} />
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              className="w-full px-4 py-3 rounded-xl bg-slate-900/40 border border-white/10 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400/50 transition-all text-sm backdrop-blur-sm"
            />
            {error && (
              <p className="text-rose-500 text-xs mt-2 flex items-center gap-1 font-medium">
                <AlertTriangle size={14} /> {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-400 hover:to-violet-400 text-white font-bold text-sm transition-all shadow-[0_0_20px_rgba(99,102,241,0.4)] focus:outline-none disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                <span>Initializing agent... <Rocket size={16} className="inline ml-1" /></span>
              </>
            ) : (
              <span className="flex items-center gap-2">Initialize Core <Rocket size={16} /></span>
            )}
          </button>
        </form>

        <div className="mt-8 border-t border-slate-800/80 pt-6 text-center">
          <p className="text-xs text-slate-500">
            Enter any email to create an isolated local session.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

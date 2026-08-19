"use client";

import React, { useState, useEffect } from "react";
import { api, SharedWebsiteItem } from "@/lib/api";
import { FolderGit2, Shield, Settings, RefreshCw } from "lucide-react";

export default function LearnedWebsites() {
  const [websites, setWebsites] = useState<SharedWebsiteItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchWebsites = async () => {
      setIsLoading(true);
      try {
        const data = await api.getLearnedWebsites();
        setWebsites(data);
      } catch (e) {
        console.error("Failed to load learned websites", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchWebsites();
  }, []);

  const parseJSON = (str: string, fallback: any = {}) => {
    try {
      return JSON.parse(str || "{}");
    } catch (e) {
      return fallback;
    }
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
          <FolderGit2 size={28} className="text-indigo-400" /> Learned Web Knowledge
        </h1>
        <p className="text-slate-300/80 text-sm mt-2">
          Review structural sitemaps and automation workflows learned dynamically by MOSAIC across the web.
        </p>
      </div>

      {/* Security notice banner */}
      <div className="glass-card border-indigo-500/30 rounded-3xl p-5 mb-8 flex items-start gap-4">
        <Shield size={24} className="text-indigo-400 shrink-0" />
        <div>
          <h4 className="font-bold text-slate-200 text-sm">Privacy Isolation Policy</h4>
          <p className="text-slate-400 text-xs mt-1 leading-relaxed">
            This dashboard displays **Shared Web Knowledge** containing only generic website layouts, workflow selectors, sitemaps, and CLI commands.
            MOSAIC enforces a strict database-level separation: **absolutely no private details** (emails, CVs, preferences, cookies, session credentials) will ever enter the global web knowledge database.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
        </div>
      ) : websites.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 border border-dashed border-white/20 rounded-3xl glass-card">
          <FolderGit2 size={40} className="mb-4 text-slate-600" />
          <h3 className="text-slate-200 font-bold text-base">No shared websites found</h3>
          <p className="text-slate-400 text-xs mt-1 text-center max-w-sm">
            Once Webcmd automates new domains successfully, the learned selectors and sitemaps will populate here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {websites.map((site) => (
            <div
              key={site.id}
              className="glass-panel hover:border-white/20 transition-all rounded-3xl p-6 space-y-5"
            >
              {/* Site Header details */}
              <div className="flex items-start justify-between border-b border-slate-800/50 pb-4">
                <div>
                  <h3 className="font-extrabold text-slate-200 text-base">{site.name}</h3>
                  <span className="text-xs text-indigo-400 font-bold font-mono">{site.domain}</span>
                </div>
                <div className="text-right">
                  <div className="text-emerald-400 font-bold text-sm">{(site.success_rate * 100).toFixed(0)}% Success</div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase">{site.uses_count} Executions</span>
                </div>
              </div>

              {/* Workflows list */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">Learned Workflows</span>
                <div className="space-y-2">
                  {Object.entries(parseJSON(site.workflows, {})).map(([name, desc]: [string, any], idx) => (
                    <div key={idx} className="bg-slate-950/60 border border-slate-850 p-2.5 rounded-xl text-xs">
                      <span className="font-bold text-indigo-400 uppercase tracking-wide text-[10px] flex items-center gap-1.5 mb-1">
                        <Settings size={12} /> {name} workflow
                      </span>
                      <p className="text-slate-300 font-medium leading-relaxed">{desc}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Commands detail */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">CLI Reusable Commands</span>
                <div className="space-y-1 bg-slate-950/80 border border-slate-900 p-3 rounded-xl">
                  {parseJSON(site.commands, []).map((cmd: string, idx: number) => (
                    <code key={idx} className="block text-slate-400 font-mono text-[10px] leading-relaxed select-all">
                      $ {cmd}
                    </code>
                  ))}
                </div>
              </div>

              {/* Fallback details */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">Adaptive Recovery Strategies</span>
                <ul className="space-y-1.5 list-inside text-xs text-slate-450 font-medium leading-relaxed pl-1">
                  {parseJSON(site.fallback_strategies, []).map((strat: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <RefreshCw size={14} className="text-amber-500 shrink-0 mt-0.5" />
                      <span>{strat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Validation dates footer */}
              <div className="text-[10px] text-slate-550 border-t border-slate-850/60 pt-4 flex justify-between font-medium">
                <span>Last Updated: {new Date(site.last_updated).toLocaleDateString()}</span>
                <span>Validated: {new Date(site.last_validated).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

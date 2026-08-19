"use client";

import React from "react";
import { Globe, Brain, Activity, FolderGit2, User, FileText, LogOut } from "lucide-react";

type TabType = "agent" | "memory" | "activity" | "websites" | "profile" | "documents";

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  email: string;
  onLogout: () => void;
}

export default function Sidebar({ activeTab, setActiveTab, email, onLogout }: SidebarProps) {
  const menuItems: { id: TabType; label: string; icon: React.ReactNode }[] = [
    { id: "agent", label: "Browser Agent", icon: <Globe size={18} /> },
    { id: "memory", label: "My Memory", icon: <Brain size={18} /> },
    { id: "activity", label: "Activity Log", icon: <Activity size={18} /> },
    { id: "websites", label: "Learned Sites", icon: <FolderGit2 size={18} /> },
    { id: "profile", label: "User Profile", icon: <User size={18} /> },
    { id: "documents", label: "Documents", icon: <FileText size={18} /> },
  ];

  return (
    <aside className="w-64 bg-black/20 backdrop-blur-2xl border-r border-white/10 flex flex-col justify-between shrink-0 h-screen shadow-2xl relative z-20">
      <div>
        {/* Sidebar Header Logo */}
        <div className="p-6 flex items-center gap-3 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.5)]">
            <span className="text-sm font-black text-white">M</span>
          </div>
          <div>
            <h2 className="font-extrabold text-slate-100 text-base leading-none">MOSAIC</h2>
            <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase">Browser Agent</span>
          </div>
        </div>

        {/* Sidebar Nav */}
        <nav className="p-4 space-y-1.5">
          {menuItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-bold transition-all border ${
                  isActive
                    ? "bg-gradient-to-r from-indigo-500/80 to-violet-500/80 border-indigo-400/50 text-white shadow-[0_0_15px_rgba(99,102,241,0.3)]"
                    : "border-transparent text-slate-300 hover:text-white hover:bg-white/5 hover:border-white/10"
                }`}
              >
                <span className="flex items-center justify-center w-5 h-5">{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Information & Action Footer */}
      <div className="p-4 border-t border-white/10 space-y-3 bg-black/10">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 text-xs">
            {email.substring(0, 2).toUpperCase()}
          </div>
          <div className="overflow-hidden min-w-0">
            <p className="text-xs font-bold text-slate-300 truncate leading-tight">{email}</p>
            <span className="text-[9px] text-indigo-400/80 font-bold uppercase tracking-wider">Active Session</span>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-bold text-rose-300 hover:text-rose-200 hover:bg-rose-500/20 border border-transparent hover:border-rose-500/30 transition-all shadow-lg hover:shadow-rose-500/20"
        >
          <LogOut size={16} /> Logout Session
        </button>
      </div>
    </aside>
  );
}

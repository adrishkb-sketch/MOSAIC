"use client";

import React from "react";

type TabType = "agent" | "memory" | "activity" | "websites" | "profile" | "documents";

interface SidebarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  email: string;
  onLogout: () => void;
}

export default function Sidebar({ activeTab, setActiveTab, email, onLogout }: SidebarProps) {
  const menuItems = [
    { id: "agent", label: "Browser Agent", icon: "🌐" },
    { id: "memory", label: "My Memory", icon: "🧠" },
    { id: "activity", label: "Activity Log", icon: "📋" },
    { id: "websites", label: "Learned Sites", icon: "🗂" },
    { id: "profile", label: "User Profile", icon: "👤" },
    { id: "documents", label: "Documents", icon: "📄" },
  ] as const;

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen">
      <div>
        {/* Sidebar Header Logo */}
        <div className="p-6 flex items-center gap-3 border-b border-slate-800/80">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center shadow shadow-indigo-500/20">
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
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  isActive
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* User Information & Action Footer */}
      <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-950/20">
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
          className="w-full flex items-center justify-center gap-2 py-2 rounded-xl text-xs font-bold text-rose-400 hover:text-rose-350 hover:bg-rose-950/20 border border-transparent hover:border-rose-900/30 transition-all"
        >
          <span>🚪</span> Logout Session
        </button>
      </div>
    </aside>
  );
}

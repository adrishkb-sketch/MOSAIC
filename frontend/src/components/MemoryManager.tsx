"use client";

import React, { useState, useEffect } from "react";
import { api, MemoryItem, MemoryWhyResponse } from "@/lib/api";
import { Brain, Save, Edit2, Trash2, Search, Shield, X, RotateCcw } from "lucide-react";
import { motion } from "framer-motion";

interface MemoryManagerProps {
  email: string;
}

export default function MemoryManager({ email }: MemoryManagerProps) {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedWhy, setSelectedWhy] = useState<MemoryWhyResponse | null>(null);
  const [whyLoading, setWhyLoading] = useState(false);
  const [editingItem, setEditingItem] = useState<MemoryItem | null>(null);
  const [editValue, setEditValue] = useState("");

  const fetchMemories = async () => {
    setIsLoading(true);
    try {
      const data = await api.getMemories(email);
      setMemories(data);
    } catch (e) {
      console.error("Failed to load memories", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [email]);

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want MOSAIC to forget this memory?")) {
      try {
        await api.deleteMemory(id);
        setMemories(memories.filter((m) => m.id !== id));
      } catch (e) {
        alert("Failed to delete memory");
      }
    }
  };

  const handleClearAll = async () => {
    if (confirm("WARNING: This will permanently delete all your saved profile details, preferences, and documents from My Memory. Proceed?")) {
      try {
        await api.clearMemories(email);
        setMemories([]);
      } catch (e) {
        alert("Failed to clear memories");
      }
    }
  };

  const handleWhyClick = async (id: number) => {
    setWhyLoading(true);
    try {
      const whyData = await api.getMemoryWhy(id);
      setSelectedWhy(whyData);
    } catch (e) {
      console.error(e);
      alert("Failed to fetch transparency logs");
    } finally {
      setWhyLoading(false);
    }
  };

  const startEdit = (item: MemoryItem) => {
    setEditingItem(item);
    setEditValue(item.value);
  };

  const saveEdit = async () => {
    if (!editingItem) return;
    try {
      const updated = await api.updateMemory(editingItem.id, { value: editValue });
      setMemories(memories.map((m) => (m.id === editingItem.id ? updated : m)));
      setEditingItem(null);
    } catch (e) {
      alert("Failed to save updates");
    }
  };

  const formatKeyName = (key: string) => {
    const spaced = key.replace(/([A-Z])/g, " $1");
    return spaced.charAt(0).toUpperCase() + spaced.slice(1);
  };

  const getClassificationColor = (cls: string) => {
    switch (cls) {
      case "SENSITIVE_USER_DATA":
        return "bg-rose-500/10 text-rose-400 border-rose-500/25";
      case "PRIVATE_USER_DATA":
        return "bg-amber-500/10 text-amber-400 border-amber-500/25";
      case "EXPLICIT_PREFERENCE":
      case "EXPLICIT_MEMORY":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/25";
      default:
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/25";
    }
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-h-screen">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
            <Brain size={28} className="text-indigo-400" /> Memory & Transparency Center
          </h1>
          <p className="text-slate-300/80 text-sm mt-2">
            Review and manage all information MOSAIC currently stores about you in your isolated space.
          </p>
        </div>
        {memories.length > 0 && (
          <button
            onClick={handleClearAll}
            className="px-4 py-2 text-xs font-bold text-rose-400 hover:text-rose-350 bg-rose-950/20 hover:bg-rose-950/40 border border-rose-900/30 rounded-xl transition-all flex items-center gap-2"
          >
            <Trash2 size={14} /> Clear My Memory
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
        </div>
      ) : memories.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 border border-dashed border-white/20 rounded-3xl glass-card">
          <Brain size={40} className="mb-4 text-slate-600" />
          <h3 className="text-slate-200 font-bold text-base">Your memory is completely empty</h3>
          <p className="text-slate-400 text-xs mt-1 text-center max-w-sm">
            Start talking to the agent or fill out your profile details to populate your private profile variables.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {memories.map((item, index) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              whileHover={{ scale: 1.02 }}
              className="glass-panel hover:border-indigo-500/30 transition-all rounded-3xl p-6 relative flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-start justify-between gap-4 mb-4">
                  <h3 className="font-extrabold text-slate-200 text-sm tracking-tight truncate max-w-[150px]">
                    {formatKeyName(item.key)}
                  </h3>
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold border ${getClassificationColor(item.classification)}`}>
                    {item.classification.replace(/_/g, " ")}
                  </span>
                </div>

                {editingItem?.id === item.id ? (
                  <textarea
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    rows={3}
                    className="w-full text-xs bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 mb-4"
                  />
                ) : (
                  <p className="text-slate-300 text-xs bg-black/30 rounded-xl p-3 border border-white/5 leading-relaxed break-words mb-4 line-clamp-4">
                    {item.value}
                  </p>
                )}

                <div className="flex items-center gap-2 mb-4">
                  <span className="text-[10px] text-slate-500 font-bold uppercase">Source:</span>
                  <span className="text-[10px] text-indigo-400 font-bold bg-indigo-500/5 px-2 py-0.5 rounded border border-indigo-500/10">
                    {item.source}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between border-t border-slate-800/50 pt-4 gap-2">
                {editingItem?.id === item.id ? (
                  <>
                    <button
                      onClick={saveEdit}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-[10px] font-bold transition-all flex items-center gap-1"
                    >
                      <Save size={12} /> Save
                    </button>
                    <button
                      onClick={() => setEditingItem(null)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-[10px] font-bold transition-all"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => handleWhyClick(item.id)}
                      className="text-[10px] font-bold text-indigo-400 hover:text-indigo-350 flex items-center gap-1"
                    >
                      <Search size={12} /> Why did MOSAIC use this?
                    </button>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => startEdit(item)}
                        className="p-1.5 text-[10px] font-bold text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all"
                        title="Edit Memory"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 text-[10px] font-bold text-rose-400 hover:text-rose-350 hover:bg-rose-950/20 rounded-lg transition-all"
                        title="Forget Memory"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Transparency Modal */}
      {selectedWhy && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-lg p-6 relative rounded-3xl">
            <button
              onClick={() => setSelectedWhy(null)}
              className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 text-lg"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-6">
              <span className="text-2xl"><Shield size={24} className="text-indigo-400" /></span>
              <div>
                <h3 className="font-extrabold text-slate-100 text-base">Data Usage Transparency Report</h3>
                <p className="text-xs text-slate-400">Auditing the private profile key: "{selectedWhy.key}"</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Stored Value</span>
                <p className="text-xs text-slate-200 font-mono break-all">{selectedWhy.value}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950/30 border border-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-0.5">Classification</span>
                  <span className="text-[11px] font-bold text-indigo-400">{selectedWhy.classification}</span>
                </div>
                <div className="bg-slate-950/30 border border-slate-800/50 rounded-xl p-3">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-0.5">Origin Source</span>
                  <span className="text-[11px] font-bold text-emerald-400">{selectedWhy.source}</span>
                </div>
              </div>

              <div className="border-y border-slate-800/80 py-4 my-2 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Shared with other users:</span>
                  <span className="font-bold text-rose-500 flex items-center gap-1">No (Always Private)</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Exported to Global Web Knowledge:</span>
                  <span className="font-bold text-rose-500 flex items-center gap-1">No (Sanitized Out)</span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">Usage Activity History</span>
                {selectedWhy.usage_history.length === 0 ? (
                  <p className="text-slate-400 text-xs bg-slate-950/20 p-3 rounded-lg border border-slate-850">
                    This memory item has not been retrieved for browser automation tasks yet.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-32 overflow-y-auto pr-1">
                    {selectedWhy.usage_history.map((log, index) => (
                      <div key={index} className="text-xs bg-slate-950/40 p-2.5 rounded-lg border border-slate-850 flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-slate-500 font-bold">
                          <span>Task ID: {log.task_id}</span>
                          <span>{new Date(log.timestamp).toLocaleString()}</span>
                        </div>
                        <p className="text-slate-300 truncate font-medium">Query: "{log.task_description}"</p>
                        {log.website && (
                          <span className="text-[10px] text-indigo-400 font-semibold">Accessed: {log.website}</span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedWhy(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all"
              >
                Close Audit Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

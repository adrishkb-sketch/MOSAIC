"use client";

import React, { useState, useEffect } from "react";
import { api, ActivityItem } from "@/lib/api";
import { ClipboardList, Search, FileJson } from "lucide-react";

interface ActivityLogProps {
  email: string;
}

export default function ActivityLog({ email }: ActivityLogProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedActivity, setSelectedActivity] = useState<ActivityItem | null>(null);

  const fetchActivities = async () => {
    setIsLoading(true);
    try {
      const data = await api.getActivities(email);
      setActivities(data);
    } catch (e) {
      console.error("Failed to fetch activities", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
  }, [email]);

  const parseJSON = (str: string, fallback: any = []) => {
    try {
      return JSON.parse(str || "[]");
    } catch (e) {
      return fallback;
    }
  };

  const getStatusBadge = (status: ActivityItem["status"]) => {
    const styles = {
      completed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
      failed: "bg-rose-500/10 text-rose-400 border-rose-500/25",
      cancelled: "bg-slate-500/10 text-slate-400 border-slate-500/25",
      browsing: "bg-blue-500/10 text-blue-400 border-blue-500/25 animate-pulse",
      thinking: "bg-indigo-500/10 text-indigo-400 border-indigo-500/25 animate-pulse",
      asking: "bg-purple-500/10 text-purple-400 border-purple-500/25 animate-pulse",
      waiting_approval: "bg-amber-500/10 text-amber-400 border-amber-500/25 animate-pulse",
    };
    return (
      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${styles[status] || styles.completed}`}>
        {status.replace(/_/g, " ").toUpperCase()}
      </span>
    );
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
          <ClipboardList size={28} className="text-indigo-400" /> Security & Activity Log
        </h1>
        <p className="text-slate-300/80 text-sm mt-2">
          Inspect a detailed history of every query, tools invoked, pages browsed, and private memories retrieved.
        </p>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
        </div>
      ) : activities.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 border border-dashed border-white/20 rounded-3xl glass-card">
          <ClipboardList size={40} className="mb-4 text-slate-600" />
          <h3 className="text-slate-200 font-bold text-base">No activity recorded yet</h3>
          <p className="text-slate-400 text-xs mt-1 text-center max-w-sm">
            Once you execute browser tasks or search queries, the audit trail will appear here.
          </p>
        </div>
      ) : (
        <div className="glass-panel overflow-hidden rounded-3xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-black/20 text-[10px] uppercase font-bold tracking-wider text-slate-300">
                <th className="px-6 py-4">Task ID</th>
                <th className="px-6 py-4">User Request</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {activities.map((log) => (
                <tr key={log.id} className="hover:bg-white/5 transition-all text-xs text-slate-200">
                  <td className="px-6 py-4 font-mono font-bold text-slate-400">{log.task_id.substring(0, 12)}...</td>
                  <td className="px-6 py-4 font-medium max-w-xs truncate">{log.request}</td>
                  <td className="px-6 py-4">{getStatusBadge(log.status)}</td>
                  <td className="px-6 py-4 text-slate-500">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => setSelectedActivity(log)}
                      className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-[10px] text-white font-extrabold rounded-lg transition-all flex items-center gap-1.5 ml-auto"
                    >
                      <Search size={12} /> Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Activity Details Modal */}
      {selectedActivity && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl p-6 relative rounded-3xl max-h-[90vh] flex flex-col">
            <h3 className="text-slate-200 font-bold text-base mb-4 flex items-center gap-2">
              <Search size={18} className="text-indigo-400" /> Event Inspection
            </h3>
            <button
              onClick={() => setSelectedActivity(null)}
              className="absolute top-4 right-4 text-slate-500 hover:text-slate-350 text-lg"
            >
              ✕
            </button>

            {/* Modal Header */}
            <div className="mb-6 shrink-0 pr-8">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xl">📋</span>
                <h3 className="font-extrabold text-slate-100 text-base">Task Audit Report</h3>
                {getStatusBadge(selectedActivity.status)}
              </div>
              <p className="text-[10px] text-slate-500 font-mono">Task ID: {selectedActivity.task_id}</p>
            </div>

            {/* Scrollable Modal Content */}
            <div className="space-y-6 overflow-y-auto pr-1 flex-1 text-xs text-slate-300">
              {/* Request Summary */}
              <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-4">
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">User Query</span>
                <p className="text-slate-200 font-medium leading-relaxed">"{selectedActivity.request}"</p>
                {selectedActivity.interpreted_intent && (
                  <div className="mt-3 pt-3 border-t border-slate-900 flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">Interpreted Intent:</span>
                    <span className="text-[10px] text-indigo-400 font-bold bg-indigo-500/5 px-2 py-0.5 rounded border border-indigo-500/10">
                      {selectedActivity.interpreted_intent}
                    </span>
                  </div>
                )}
              </div>

              {/* Scope/Private Memory Used */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">Private Memories Retrieved</span>
                {parseJSON(selectedActivity.information_used).length === 0 ? (
                  <p className="text-slate-500 text-[11px] italic">No private memory keys were retrieved or sent during this task.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {parseJSON(selectedActivity.information_used).map((key: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-850 text-indigo-400 font-semibold font-mono text-[10px]"
                      >
                        🧠 {key}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Websites Accessed */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-2">Websites Browsed</span>
                {parseJSON(selectedActivity.websites_visited).length === 0 ? (
                  <p className="text-slate-500 text-[11px] italic">No external websites were browsed during this task.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {parseJSON(selectedActivity.websites_visited).map((site: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-2 py-1 rounded bg-slate-950 border border-slate-850 text-blue-400 font-semibold text-[10px]"
                      >
                        🌐 {site}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Steps/Timeline */}
              <div>
                <span className="text-[10px] text-slate-500 font-bold uppercase block mb-3">Orchestration Steps Execution Log</span>
                <div className="space-y-3 relative border-l border-slate-800/80 ml-3 pl-4">
                  {parseJSON(selectedActivity.steps).map((step: any, idx: number) => (
                    <div key={idx} className="relative">
                      {/* Circle indicator */}
                      <span className="absolute -left-[21px] top-1.5 w-2 h-2 rounded-full bg-indigo-500 border border-slate-900" />
                      
                      <div className="bg-slate-950/40 border border-slate-850 rounded-xl p-3.5 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-slate-500 font-bold">
                          <span>STEP #{idx + 1} - {step.action?.toUpperCase() || "ACTION"}</span>
                          {step.timestamp && <span>{new Date(step.timestamp).toLocaleTimeString()}</span>}
                        </div>
                        <p className="text-slate-200 font-medium text-xs leading-relaxed">{step.description || step.details}</p>
                        
                        {step.tool && (
                          <div className="flex items-center gap-1.5 mt-2">
                            <span className="text-[9px] text-slate-500 uppercase font-bold">Tool used:</span>
                            <span className="text-[9px] font-bold text-slate-400 bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded font-mono">
                              {step.tool}
                            </span>
                          </div>
                        )}
                        {step.error && (
                          <div className="mt-2 bg-rose-500/10 text-rose-400 border border-rose-500/25 p-2 rounded-lg text-[10px] leading-relaxed">
                            <span className="font-bold">Error/Exception:</span> {step.error}
                          </div>
                        )}
                        {step.recovery && (
                          <div className="mt-2 bg-amber-500/10 text-amber-400 border border-amber-500/25 p-2 rounded-lg text-[10px] leading-relaxed">
                            <span className="font-bold">🔄 Recovery Action:</span> {step.recovery}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Task Result Summary */}
              {selectedActivity.result && (
                <div className="bg-slate-950/40 border border-slate-800/80 rounded-xl p-4">
                  <span className="text-[10px] text-slate-500 font-bold uppercase block mb-1">Final Result</span>
                  <p className="text-slate-100 font-medium leading-relaxed font-sans">{selectedActivity.result}</p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="mt-6 shrink-0 pt-4 border-t border-slate-800/85 flex justify-end">
              <button
                onClick={() => setSelectedActivity(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

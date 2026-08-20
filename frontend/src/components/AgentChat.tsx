"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, ChatMessage, ActionPlanItem, SearchResultItem, InteractiveOptionItem } from "@/lib/api";
import { Brain, Globe, HelpCircle, Settings, Hourglass, RefreshCw, CheckCircle, XCircle, Sparkles, StopCircle, Shield, Zap, Send, KeyRound, Check, ChevronRight, ChevronDown, ChevronUp } from "lucide-react";

import { motion, AnimatePresence } from "framer-motion";

interface AgentChatProps {
  email: string;
  setGlobalStatus?: (status: "idle" | "browsing" | "error") => void;
}

export default function AgentChat({ email, setGlobalStatus }: AgentChatProps) {
  const [showLiveViewport, setShowLiveViewport] = useState(true);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [sortOrder, setSortOrder] = useState<string>("default");
  const [currentAction, setCurrentAction] = useState<string | null>(null);
  const [otpInput, setOtpInput] = useState("");
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "agent",
      text: "Hello! I am MOSAIC, your personal browser agent. I can help you search for books, research products, apply for jobs, or automate multi-step checkout processes safely. What would you like to achieve today?",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<
    "idle" | "thinking" | "asking" | "browsing" | "learning" | "preparing" | "waiting_approval" | "completed" | "failed" | "recovering"
  >("idle");
  const [isLoading, setIsLoading] = useState(false);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [browserUrl, setBrowserUrl] = useState<string | null>(null);
  const [browserActive, setBrowserActive] = useState(false);

  // Action Plan states
  const [actionPlan, setActionPlan] = useState<any>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, status, actionPlan]);

  useEffect(() => {
    if (setGlobalStatus) {
      if (["failed", "waiting_approval"].includes(status)) {
        setGlobalStatus("error");
      } else if (["browsing", "learning", "thinking", "preparing"].includes(status)) {
        setGlobalStatus("browsing");
      } else {
        setGlobalStatus("idle");
      }
    }
  }, [status, setGlobalStatus]);

  const sendQuery = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      sender: "user",
      text: queryText,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStatus("thinking");

    try {
      const response = await api.chat(email, userMessage.text, taskId || undefined);
      
      if (response.task_id) setTaskId(response.task_id);
      setBrowserActive(response.browser_active);
      if (response.browser_url) setBrowserUrl(response.browser_url);
      if (response.screenshot) setScreenshot(response.screenshot);
      if (response.current_action) setCurrentAction(response.current_action);

      // Add agent reply
      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date(),
          results: response.results,
          options: response.options,
          current_action: response.current_action
        }
      ]);

      if (response.action_plan_required && response.action_plan) {
        setActionPlan(response.action_plan);
        setStatus("waiting_approval");
      } else if (response.clarification_needed) {
        setStatus("asking");
      } else if (response.browser_active) {
        setStatus("browsing");
      } else if (response.status === "completed") {
        setStatus("completed");
      } else {
        setStatus("idle");
      }
    } catch (e: any) {
      console.error(e);
      setStatus("failed");
      setMessages((prev) => [
        ...prev,
        {
          sender: "system",
          text: `An error occurred: ${e.message || "Unknown error"}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const text = input;
    setInput("");
    await sendQuery(text);
  };

  const handleSelectOption = async (option: InteractiveOptionItem) => {
    await sendQuery(`Select option: ${option.title}`);
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otpInput.trim()) return;
    const otp = otpInput;
    setOtpInput("");
    await sendQuery(otp);
  };

  const handleApply = async (title: string, url: string) => {
    setInput("");
    setIsLoading(true);
    setStatus("browsing");
    setBrowserActive(true);
    setBrowserUrl(url);

    const userMessage: ChatMessage = {
      sender: "user",
      text: `Automate for ${title}`,
      timestamp: new Date()
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await api.chat(email, `apply_for: ${url}`, taskId || undefined);
      
      if (response.task_id) setTaskId(response.task_id);
      setBrowserActive(response.browser_active);
      if (response.browser_url) setBrowserUrl(response.browser_url);
      if (response.screenshot) setScreenshot(response.screenshot);
      if (response.current_action) setCurrentAction(response.current_action);

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date(),
          results: response.results,
          options: response.options,
          current_action: response.current_action
        }
      ]);

      if (response.action_plan_required && response.action_plan) {
        setActionPlan(response.action_plan);
        setStatus("waiting_approval");
      } else if (response.clarification_needed) {
        setStatus("asking");
      } else if (response.browser_active) {
        setStatus("browsing");
      } else if (response.status === "completed") {
        setStatus("completed");
      } else {
        setStatus("idle");
      }
    } catch (e: any) {
      console.error(e);
      setStatus("failed");
      setMessages((prev) => [
        ...prev,
        {
          sender: "system",
          text: `Automation failed: ${e.message || "Unknown error"}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveAction = async (approved: boolean) => {
    if (!taskId) return;
    setIsLoading(true);
    setStatus("preparing");

    try {
      const result = await api.approveActionPlan(taskId, approved);
      
      setMessages((prev) => [
        ...prev,
        {
          sender: "system",
          text: approved ? "✓ Action plan approved. Initiating final execution..." : "❌ Action plan rejected by user.",
          timestamp: new Date()
        }
      ]);

      setActionPlan(null);

      // Send a follow-up request to continue the task
      const followUpMsg = approved ? "proceed_execution" : "cancel_execution";
      const response = await api.chat(email, followUpMsg, taskId);

      setBrowserActive(response.browser_active);
      if (response.browser_url) setBrowserUrl(response.browser_url);
      if (response.screenshot) setScreenshot(response.screenshot);
      if (response.current_action) setCurrentAction(response.current_action);

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date(),
          options: response.options
        }
      ]);

      if (response.status === "completed") {
        setStatus("completed");
      } else {
        setStatus("idle");
      }
    } catch (e: any) {
      console.error(e);
      setStatus("failed");
      setMessages((prev) => [
        ...prev,
        {
          sender: "system",
          text: `Approval handling failed: ${e.message}`,
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelTask = async () => {
    setStatus("idle");
    setTaskId(null);
    setActionPlan(null);
    setBrowserActive(false);
    setScreenshot(null);
    setBrowserUrl(null);
    setCurrentAction(null);
    setMessages((prev) => [
      ...prev,
      {
        sender: "system",
        text: "🚨 Task cancelled by user. Browser session closed.",
        timestamp: new Date()
      }
    ]);
  };

  const getStatusText = () => {
    switch (status) {
      case "thinking": return <span className="flex items-center gap-1.5"><Brain size={14} /> Thinking & Reasoning...</span>;
      case "browsing": return <span className="flex items-center gap-1.5"><Globe size={14} /> Browsing Real Webpage...</span>;
      case "asking": return <span className="flex items-center gap-1.5"><HelpCircle size={14} /> Awaiting your choice / input...</span>;
      case "learning": return <span className="flex items-center gap-1.5"><Brain size={14} /> Inspecting site structure...</span>;
      case "preparing": return <span className="flex items-center gap-1.5"><Settings size={14} /> Preparing execution...</span>;
      case "waiting_approval": return <span className="flex items-center gap-1.5"><Hourglass size={14} /> Awaiting your approval...</span>;
      case "recovering": return <span className="flex items-center gap-1.5"><RefreshCw size={14} /> Recovering...</span>;
      case "completed": return <span className="flex items-center gap-1.5"><CheckCircle size={14} /> Task completed!</span>;
      case "failed": return <span className="flex items-center gap-1.5"><XCircle size={14} /> Task failed.</span>;
      default: return <span className="flex items-center gap-1.5"><Sparkles size={14} /> Ready</span>;
    }
  };

  const isViewportVisible = browserActive || (showLiveViewport && (status !== "idle" && status !== "completed" && status !== "failed")) || screenshot !== null;

  return (
    <div className="flex-1 flex overflow-hidden h-screen bg-transparent">
      {/* Left Pane: Conversational Log */}
      <div className={`flex flex-col border-r border-white/10 transition-all duration-300 ${isViewportVisible ? "w-1/2 bg-black/20 backdrop-blur-sm" : "w-full"}`}>
        {/* Header Status */}
        <div className="p-4 border-b border-white/10 bg-black/20 backdrop-blur-md flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`w-2.5 h-2.5 rounded-full ${status === "idle" ? "bg-slate-500" : status === "completed" ? "bg-emerald-500" : "bg-indigo-500 animate-ping"}`} />
            <div>
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">{getStatusText()}</span>
              {currentAction && <p className="text-[10px] text-indigo-400 font-medium mt-0.5">{currentAction}</p>}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showLiveViewport}
                onChange={(e) => setShowLiveViewport(e.target.checked)}
                className="sr-only peer"
              />
              <div className="relative w-7 h-4 bg-slate-800 rounded-full peer peer-focus:ring-1 peer-focus:ring-indigo-500 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:start-[2px] after:bg-slate-400 peer-checked:after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-600"></div>
              <span className="text-[10px] font-bold text-slate-400 peer-checked:text-slate-200">Live Viewport</span>
            </label>
            
            {status !== "idle" && (
              <button
                onClick={handleCancelTask}
                className="px-2.5 py-1 text-[10px] font-bold text-rose-400 hover:text-rose-350 bg-rose-950/20 border border-rose-900/30 rounded-lg transition-all flex-shrink-0 flex items-center gap-1.5"
              >
                <StopCircle size={14} /> Stop Agent
              </button>
            )}
          </div>
        </div>

        {/* Messages list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((msg, index) => {
            const isAgent = msg.sender === "agent";
            const isSystem = msg.sender === "system";
            return (
              <motion.div 
                key={index} 
                initial={{ opacity: 0, y: 15, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, type: "spring", stiffness: 200, damping: 20 }}
                className={`flex ${isAgent ? "justify-start" : isSystem ? "justify-center" : "justify-end"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed shadow-sm ${
                    isAgent
                      ? "glass-card text-slate-100"
                      : isSystem
                      ? "bg-black/30 border border-white/5 text-slate-400 text-center font-semibold backdrop-blur-sm"
                      : "bg-gradient-to-r from-indigo-500 to-violet-500 text-white font-bold shadow-[0_0_15px_rgba(99,102,241,0.4)]"
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>

                  {/* Interactive Options Cards */}
                  {isAgent && msg.options && msg.options.length > 0 && (
                    <div className="mt-4 space-y-2 border-t border-white/10 pt-3">
                      <p className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">Recommended Options:</p>
                      <div className="grid grid-cols-1 gap-2">
                        {msg.options.map((opt) => (
                          <button
                            key={opt.id}
                            disabled={isLoading}
                            onClick={() => handleSelectOption(opt)}
                            className="w-full text-left p-3 rounded-xl bg-slate-900/80 hover:bg-indigo-950/40 border border-white/10 hover:border-indigo-500/50 transition-all flex items-center justify-between gap-3 group"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                                  {opt.id}
                                </span>
                                <h5 className="font-bold text-slate-100 text-xs group-hover:text-indigo-300 transition-colors">{opt.title}</h5>
                              </div>
                              {opt.description && (
                                <p className="text-[10px] text-slate-400 mt-1 ml-7">{opt.description}</p>
                              )}
                            </div>
                            <ChevronRight size={16} className="text-slate-500 group-hover:text-indigo-400 transition-transform group-hover:translate-x-1" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Search Results List */}
                  {isAgent && msg.results && msg.results.length > 0 && (() => {
                    let filtered = msg.results.filter(res => {
                      if (activeFilter === "all") return true;
                      if (activeFilter === "shopping") return res.type === "shopping";
                      if (activeFilter === "job") return res.type === "job";
                      if (activeFilter === "event") return res.type === "event";
                      return true;
                    });
                    
                    return (
                      <div className="mt-4 space-y-3 border-t border-white/10 pt-3">
                        <div className="flex items-center justify-between flex-wrap gap-2">
                          <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Direct Store & Action Links ({filtered.length}):</p>
                        </div>
                        
                        <div className="grid grid-cols-1 gap-2.5">
                          {filtered.map((res, rIdx) => (
                            <div key={rIdx} className="bg-slate-950 border border-white/5 rounded-xl p-3 flex flex-col justify-between gap-3 hover:border-white/15 hover:shadow-[0_4px_12px_rgba(255,255,255,0.02)] transition-all duration-300">
                              <div>
                                <div className="flex items-center justify-between gap-2">
                                  <h4 className="font-bold text-white text-[11px] leading-tight line-clamp-1 flex-1">{res.title}</h4>
                                  {res.type && (
                                    <span className="text-[8px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider bg-emerald-950/45 text-emerald-400 border border-emerald-900/30">
                                      {res.type}
                                    </span>
                                  )}
                                </div>
                                
                                {(res.price || res.stipend || res.company || res.location) && (
                                  <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 mt-2.5 pt-2.5 border-t border-white/5 text-[9px]">
                                    {res.company && <div className="text-slate-400 font-medium">🏪 <span className="text-slate-200 ml-1">{res.company}</span></div>}
                                    {res.price && <div className="text-slate-400 font-extrabold text-emerald-400">💵 Price: <span className="text-emerald-350 font-extrabold ml-1">{res.price}</span></div>}
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <a
                                  href={res.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="glass-button px-2.5 py-1.5 text-[10px] text-slate-200 font-bold rounded-lg transition-all text-center flex-1 flex items-center justify-center gap-1.5"
                                >
                                  <Globe size={12} /> View Web
                                </a>
                                <button
                                  onClick={() => handleApply(res.title, res.url)}
                                  className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-[10px] text-white font-extrabold rounded-lg transition-all text-center flex-1 flex items-center justify-center gap-1.5 shadow-[0_0_10px_rgba(99,102,241,0.3)]"
                                >
                                  <Zap size={12} /> Automate via MOSAIC
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}
                  <span className="text-[9px] text-slate-400/85 block mt-2 text-right">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </motion.div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Dedicated OTP Input Prompt */}
        {status === "asking" && currentAction?.toLowerCase().includes("otp") && (
          <div className="p-4 border-t border-indigo-500/30 bg-indigo-950/40 backdrop-blur-md">
            <form onSubmit={handleOtpSubmit} className="flex gap-2 items-center">
              <div className="flex items-center gap-2 text-indigo-300 font-bold text-xs flex-shrink-0">
                <KeyRound size={16} /> Enter OTP:
              </div>
              <input
                type="text"
                placeholder="e.g. 583920"
                value={otpInput}
                onChange={(e) => setOtpInput(e.target.value)}
                disabled={isLoading}
                autoFocus
                className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-indigo-500/50 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-400 text-xs font-mono tracking-widest text-center"
              />
              <button
                type="submit"
                disabled={isLoading || !otpInput.trim()}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-1.5"
              >
                Submit OTP <Check size={14} />
              </button>
            </form>
          </div>
        )}

        {/* Action Plan Approval Overlay */}
        {actionPlan && (
          <div className="p-4 border-t border-white/10 glass-panel space-y-4 rounded-t-3xl">
            <div className="border border-indigo-500/30 bg-indigo-950/20 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400 font-extrabold text-xs">
                <Shield size={16} /> ACTION PREVIEW REQUIRED
              </div>
              <p className="text-slate-300 text-xs">
                MOSAIC has prepared checkout inputs on <span className="font-semibold text-white">{actionPlan.website}</span>.
                Review the fields mapping and parameters before submission.
              </p>
              
              <div className="bg-slate-950 border border-slate-850 rounded-lg p-3 text-[11px] font-mono text-slate-350 space-y-1.5">
                <div><span className="text-slate-500">Goal:</span> {actionPlan.goal}</div>
                <div><span className="text-slate-500">Risk Level:</span> <span className="text-rose-400 font-semibold">{actionPlan.risk_level}</span></div>
                <div><span className="text-slate-500">Shared Data:</span> {JSON.stringify(actionPlan.information_to_be_sent)}</div>
                {actionPlan.risk_level === "HIGH_RISK" && (
                  <div className="text-rose-400 bg-rose-950/20 border border-rose-900/20 p-2 rounded mt-2 font-sans text-[10px] leading-relaxed">
                    ⚠️ **Payment Safety Rule Enforced:** MOSAIC does not automate final payments or request bank PINs. Complete the payment screen manually inside the browser.
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleApproveAction(true)}
                  disabled={isLoading}
                  className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
                >
                  Approve & Execute Action
                </button>
                <button
                  onClick={() => handleApproveAction(false)}
                  disabled={isLoading}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs rounded-xl border border-slate-750 transition-all disabled:opacity-50"
                >
                  Cancel Plan
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Regular Input box */}
        {!actionPlan && (
          <form onSubmit={handleSendMessage} className="p-4 border-t border-white/10 bg-black/20 backdrop-blur-md flex gap-2">
            <input
              type="text"
              placeholder="Ask MOSAIC: 'buy a good bengali book', 'recommend laptops', 'apply for jobs'..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-900/40 border border-white/10 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400/50 transition-all text-xs backdrop-blur-sm shadow-inner"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-5 py-3 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-400 hover:to-violet-400 text-white font-bold text-xs rounded-xl transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(99,102,241,0.4)] flex items-center gap-2"
            >
              Send <Send size={14} />
            </button>
          </form>
        )}
      </div>

      {/* Right Pane: Browser Viewport Split-Screen */}
      {isViewportVisible && (
        <div className="w-1/2 bg-black/40 backdrop-blur-xl flex flex-col h-full border-l border-white/10">
          <div className="p-3 border-b border-white/10 flex items-center justify-between text-xs text-slate-300 font-bold bg-black/20">
            <div className="flex items-center gap-2 truncate pr-2">
              <Globe size={16} className="text-emerald-400 flex-shrink-0" />
              <span className="font-mono text-[10px] truncate">{browserUrl || "Live Browser Active"}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {browserActive && (
                <div className="flex items-center gap-1 bg-slate-900 border border-white/10 rounded-lg p-0.5">
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => sendQuery("scroll up")}
                    title="Scroll Up Live Page"
                    className="p-1 rounded hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-300 text-[10px] font-bold transition-all disabled:opacity-50"
                  >
                    <ChevronUp size={14} />
                  </button>
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => sendQuery("scroll down")}
                    title="Scroll Down Live Page"
                    className="p-1 rounded hover:bg-indigo-600/30 text-slate-300 hover:text-indigo-300 text-[10px] font-bold transition-all disabled:opacity-50"
                  >
                    <ChevronDown size={14} />
                  </button>
                </div>
              )}
              {currentAction && (
                <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
                  {currentAction}
                </span>
              )}
              <span className="font-bold text-[9px] uppercase tracking-wider bg-slate-850 px-2 py-0.5 rounded text-slate-400">
                Live Viewport
              </span>
            </div>
          </div>

          <div className="flex-1 bg-slate-950 p-4 overflow-y-auto overflow-x-hidden relative flex flex-col items-center">
            {screenshot ? (
              <div className="w-full flex flex-col items-center space-y-4">
                <img
                  src={screenshot}
                  alt="Live browser screenshot"
                  className="w-full max-w-full h-auto border border-slate-800 rounded-xl shadow-2xl object-contain select-none transition-all duration-300"
                />
              </div>
            ) : (
              <div className="m-auto text-center space-y-3">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500 mx-auto" />
                <p className="text-slate-400 text-[11px] uppercase font-bold tracking-wider">
                  Streaming Live Browser Automation...
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


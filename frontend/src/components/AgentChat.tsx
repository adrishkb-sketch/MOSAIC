"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, ChatMessage, ActionPlanItem, SearchResultItem } from "@/lib/api";

interface AgentChatProps {
  email: string;
}

export default function AgentChat({ email }: AgentChatProps) {
  const [showLiveViewport, setShowLiveViewport] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "agent",
      text: "Hello! I am MOSAIC, your personal browser agent. I can help you search for internships, research products, registry for events, or automate repetitive web tasks. What would you like to achieve today?",
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
  }, [messages, status]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      sender: "user",
      text: input,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setStatus("thinking");

    try {
      const response = await api.chat(email, userMessage.text, taskId || undefined);
      
      // Update state based on agent response
      if (response.task_id) setTaskId(response.task_id);
      setBrowserActive(response.browser_active);
      if (response.browser_url) setBrowserUrl(response.browser_url);
      if (response.screenshot) setScreenshot(response.screenshot);

      // Add agent reply
      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date(),
          results: response.results
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

  const handleApply = async (title: string, url: string) => {
    setInput("");
    setIsLoading(true);
    setStatus("browsing");

    const userMessage: ChatMessage = {
      sender: "user",
      text: `Apply for ${title}`,
      timestamp: new Date()
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await api.chat(email, `apply_for: ${url}`, taskId || undefined);
      
      if (response.task_id) setTaskId(response.task_id);
      setBrowserActive(response.browser_active);
      if (response.browser_url) setBrowserUrl(response.browser_url);
      if (response.screenshot) setScreenshot(response.screenshot);

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date(),
          results: response.results
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
          text: `Apply automation failed: ${e.message || "Unknown error"}`,
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

      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: response.response,
          timestamp: new Date()
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
    // Clear agent execution state
    setStatus("idle");
    setTaskId(null);
    setActionPlan(null);
    setBrowserActive(false);
    setScreenshot(null);
    setBrowserUrl(null);
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
      case "thinking": return "Thinking...";
      case "browsing": return "Browsing Web...";
      case "asking": return "Awaiting input...";
      case "learning": return "Learning site structure...";
      case "preparing": return "Preparing checkout...";
      case "waiting_approval": return "Awaiting your approval...";
      case "recovering": return "Recovering from DOM drift...";
      case "completed": return "Task completed!";
      case "failed": return "Task failed.";
      default: return "Ready";
    }
  };

  const isViewportVisible = browserActive || (showLiveViewport && (status !== "idle" && status !== "completed" && status !== "failed"));

  return (
    <div className="flex-1 flex overflow-hidden h-screen bg-slate-950">
      {/* Left Pane: Conversational Log */}
      <div className={`flex flex-col border-r border-slate-800/80 transition-all duration-300 ${isViewportVisible ? "w-1/2" : "w-full"}`}>
        {/* Header Status */}
        <div className="p-4 border-b border-slate-800/80 bg-slate-900/40 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`w-2.5 h-2.5 rounded-full ${status === "idle" ? "bg-slate-500" : status === "completed" ? "bg-emerald-500" : "bg-indigo-500 animate-ping"}`} />
            <div>
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">{getStatusText()}</span>
              {taskId && <p className="text-[9px] text-slate-500 font-mono mt-0.5">Session: {taskId.substring(0, 15)}...</p>}
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
              <span className="text-[10px] font-bold text-slate-400 peer-checked:text-slate-200">Show live browser automation</span>
            </label>
            
            {status !== "idle" && (
              <button
                onClick={handleCancelTask}
                className="px-2.5 py-1 text-[10px] font-bold text-rose-400 hover:text-rose-350 bg-rose-950/20 border border-rose-900/30 rounded-lg transition-all flex-shrink-0"
              >
                🛑 Stop Agent
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
              <div key={index} className={`flex ${isAgent ? "justify-start" : isSystem ? "justify-center" : "justify-end"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-xs leading-relaxed shadow-sm ${
                    isAgent
                      ? "bg-slate-900 border border-slate-800 text-slate-100"
                      : isSystem
                      ? "bg-slate-950/40 border border-slate-850/60 text-slate-400 text-center font-semibold"
                      : "bg-indigo-600 text-white font-medium"
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>
                  {isAgent && msg.results && msg.results.length > 0 && (
                    <div className="mt-4 space-y-2 border-t border-slate-800 pt-3">
                      <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Search Results:</p>
                      <div className="grid grid-cols-1 gap-2.5">
                        {msg.results.map((res, rIdx) => (
                          <div key={rIdx} className="bg-slate-950 border border-slate-850 rounded-xl p-3 flex flex-col justify-between gap-3 hover:border-slate-800 transition-all">
                            <div>
                              <h4 className="font-bold text-white text-[11px] leading-tight line-clamp-1">{res.title}</h4>
                              <p className="text-slate-400 text-[10px] mt-1 line-clamp-2">{res.description}</p>
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <a
                                href={res.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-2.5 py-1.5 bg-slate-850 hover:bg-slate-800 border border-slate-800 text-[10px] text-slate-300 font-bold rounded-lg transition-all text-center flex-1"
                              >
                                🌐 View Website
                              </a>
                              <button
                                onClick={() => handleApply(res.title, res.url)}
                                className="px-2.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-[10px] text-white font-extrabold rounded-lg transition-all text-center flex-1 flex items-center justify-center gap-1"
                              >
                                ⚡ Apply via MOSAIC
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <span className="text-[9px] text-slate-400/85 block mt-2 text-right">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Action Plan Approval Overlay */}
        {actionPlan && (
          <div className="p-4 border-t border-slate-800 bg-slate-900/80 backdrop-blur-md space-y-4">
            <div className="border border-indigo-500/20 bg-indigo-950/10 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400 font-extrabold text-xs">
                <span>🛡</span> ACTION PREVIEW REQUIRED
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
                    ⚠️ **Payment Rule Enforced:** MOSAIC does not automate final payments or request bank PINs. Complete the payment screen manually inside the browser.
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

        {/* Input box */}
        {!actionPlan && (
          <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800/80 bg-slate-900/20 flex gap-2">
            <input
              type="text"
              placeholder="Ask MOSAIC to find internships, compare tables, or register for events..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all text-xs"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-xl transition-all disabled:opacity-50"
            >
              Send
            </button>
          </form>
        )}
      </div>

      {/* Right Pane: Browser Viewport Split-Screen */}
      {isViewportVisible && (
        <div className="w-1/2 bg-slate-900 flex flex-col h-full border-l border-slate-850">
          <div className="p-3 bg-slate-950 border-b border-slate-850 flex items-center justify-between text-xs text-slate-400 font-medium">
            <div className="flex items-center gap-2 truncate pr-4">
              <span className="text-emerald-400 text-base">🟢</span>
              <span className="font-mono text-[10px] truncate">{browserUrl || "Loading Page..."}</span>
            </div>
            <span className="font-bold text-[9px] uppercase tracking-wider bg-slate-850 px-2 py-0.5 rounded text-slate-400">
              Live Viewport
            </span>
          </div>

          <div className="flex-1 bg-slate-950 flex items-center justify-center p-4 overflow-hidden relative">
            {screenshot ? (
              <img
                src={screenshot}
                alt="Live browser screenshot"
                className="max-w-full max-h-full border border-slate-800 rounded-xl shadow-2xl object-contain select-none"
              />
            ) : (
              <div className="text-center space-y-3">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500 mx-auto" />
                <p className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">
                  Attaching browser session...
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

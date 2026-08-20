"use client";

import React, { useState, useEffect } from "react";
import LandingPage from "@/components/landing/LandingPage";
import InteractiveBackground from "@/components/landing/InteractiveBackground";
import Sidebar from "@/components/Sidebar";
import AgentChat from "@/components/AgentChat";
import MemoryManager from "@/components/MemoryManager";
import ActivityLog from "@/components/ActivityLog";
import LearnedWebsites from "@/components/LearnedWebsites";
import ProfileForm from "@/components/ProfileForm";
import DocumentManager from "@/components/DocumentManager";
import { AnimatePresence, motion } from "framer-motion";

type TabType = "agent" | "memory" | "activity" | "websites" | "profile" | "documents";

export default function DashboardPage() {
  const [email, setEmail] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("agent");
  const [globalStatus, setGlobalStatus] = useState<"idle" | "browsing" | "error">("idle");
  const [isClient, setIsClient] = useState(false);

  // Sync email from localStorage on mount (client-side only)
  useEffect(() => {
    setIsClient(true);
    const savedEmail = localStorage.getItem("mosaic_user_email");
    if (savedEmail) {
      setEmail(savedEmail);
    }
  }, []);

  const handleLogin = (userEmail: string) => {
    localStorage.setItem("mosaic_user_email", userEmail);
    setEmail(userEmail);
    setActiveTab("agent");
  };

  const handleLogout = () => {
    localStorage.removeItem("mosaic_user_email");
    setEmail(null);
  };

  if (!isClient) {
    return (
      <div className="flex-1 bg-transparent flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
      </div>
    );
  }

  // Render Landing Page if email is not set
  if (!email) {
    return <LandingPage onLogin={handleLogin} />;
  }

  // Render correct tab view
  const renderTabContent = () => {
    switch (activeTab) {
      case "agent":
        return <AgentChat email={email} setGlobalStatus={setGlobalStatus} />;
      case "memory":
        return <MemoryManager email={email} />;
      case "activity":
        return <ActivityLog email={email} />;
      case "websites":
        return <LearnedWebsites />;
      case "profile":
        return <ProfileForm email={email} />;
      case "documents":
        return <DocumentManager email={email} />;
      default:
        return <AgentChat email={email} setGlobalStatus={setGlobalStatus} />;
    }
  };

  return (
    <div className="flex-grow flex h-screen overflow-hidden bg-transparent text-slate-100 font-sans relative">
      <InteractiveBackground status={globalStatus === "browsing" ? "browsing" : globalStatus === "error" ? "error" : "idle"} />
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        email={email}
        onLogout={handleLogout}
      />
      <main className="flex-1 flex flex-col overflow-hidden bg-transparent relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col overflow-hidden"
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

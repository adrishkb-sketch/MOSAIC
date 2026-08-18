"use client";

import React, { useState, useEffect } from "react";
import LoginSplash from "@/components/LoginSplash";
import Sidebar from "@/components/Sidebar";
import AgentChat from "@/components/AgentChat";
import MemoryManager from "@/components/MemoryManager";
import ActivityLog from "@/components/ActivityLog";
import LearnedWebsites from "@/components/LearnedWebsites";
import ProfileForm from "@/components/ProfileForm";
import DocumentManager from "@/components/DocumentManager";

type TabType = "agent" | "memory" | "activity" | "websites" | "profile" | "documents";

export default function DashboardPage() {
  const [email, setEmail] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("agent");
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
      <div className="flex-1 bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
      </div>
    );
  }

  // Render Login Splash if email is not set
  if (!email) {
    return <LoginSplash onLogin={handleLogin} />;
  }

  // Render correct tab view
  const renderTabContent = () => {
    switch (activeTab) {
      case "agent":
        return <AgentChat email={email} />;
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
        return <AgentChat email={email} />;
    }
  };

  return (
    <div className="flex-grow flex h-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        email={email}
        onLogout={handleLogout}
      />
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        {renderTabContent()}
      </main>
    </div>
  );
}

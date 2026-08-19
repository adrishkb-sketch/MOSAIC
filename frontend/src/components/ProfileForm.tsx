"use client";

import React, { useState, useEffect } from "react";
import { api, MemoryItem } from "@/lib/api";

interface ProfileFormProps {
  email: string;
}

export default function ProfileForm({ email }: ProfileFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    address: "",
    college: "",
    degree: "",
    cgpa: "",
    skills: "",
    experience: "",
    github: "",
    linkedin: ""
  });
  const [memoryIds, setMemoryIds] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const fetchProfileData = async () => {
    setIsLoading(true);
    try {
      const memories = await api.getMemories(email);
      const newFormData = { ...formData };
      const ids: Record<string, number> = {};

      memories.forEach((item) => {
        if (item.key in newFormData) {
          (newFormData as any)[item.key] = item.value;
          ids[item.key] = item.id;
        }
      });
      setFormData(newFormData);
      setMemoryIds(ids);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
  }, [email]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const keys = Object.keys(formData);
      for (const key of keys) {
        const val = (formData as any)[key];
        
        // Only save if we have a value or if there is already a memory ID for it
        if (val || memoryIds[key]) {
          let classification = "PRIVATE_USER_DATA";
          if (["name", "email", "phone", "address"].includes(key)) {
            classification = "SENSITIVE_USER_DATA";
          }
          
          await api.addMemory(email, {
            key,
            value: val,
            classification,
            source: "explicit"
          });
        }
      }
      
      setSaveSuccess(true);
      await fetchProfileData();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error(e);
      alert("Failed to save profile details");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-indigo-500" />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
          👤 Universal Profile
        </h1>
        <p className="text-slate-300/80 text-sm mt-2">
          Provide your information once. MOSAIC will retrieve these details when mapping form fields, protecting your credentials.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6 max-w-4xl">
        {/* Section 1: Basic details */}
        <div className="glass-panel rounded-3xl p-6 space-y-4">
          <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase border-b border-white/10 pb-2 flex items-center gap-2">
            <span>ℹ️</span> Basic Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Full Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Email Address</label>
              <input
                type="email"
                value={email}
                disabled
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-500 cursor-not-allowed text-xs font-semibold"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Phone Number</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+1 555 0199"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Current Location</label>
              <input
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
                placeholder="Kolkata, West Bengal"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Education */}
        <div className="glass-panel rounded-3xl p-6 space-y-4">
          <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase border-b border-white/10 pb-2 flex items-center gap-2">
            <span>🎓</span> Academic Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">College / University</label>
              <input
                type="text"
                name="college"
                value={formData.college}
                onChange={handleChange}
                placeholder="Indian Institute of Technology"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Degree / Major</label>
              <input
                type="text"
                name="degree"
                value={formData.degree}
                onChange={handleChange}
                placeholder="B.Tech Computer Science"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">CGPA / GPA</label>
              <input
                type="text"
                name="cgpa"
                value={formData.cgpa}
                onChange={handleChange}
                placeholder="8.9 / 10"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
          </div>
        </div>

        {/* Section 3: Professional detail */}
        <div className="glass-panel rounded-3xl p-6 space-y-4">
          <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase border-b border-white/10 pb-2 flex items-center gap-2">
            <span>💼</span> Professional Profile & Links
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Skills (Comma-separated)</label>
              <input
                type="text"
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                placeholder="Python, React, TypeScript, C++, Machine Learning"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">GitHub Profile URL</label>
                <input
                  type="url"
                  name="github"
                  value={formData.github}
                  onChange={handleChange}
                  placeholder="https://github.com/username"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">LinkedIn Profile URL</label>
                <input
                  type="url"
                  name="linkedin"
                  value={formData.linkedin}
                  onChange={handleChange}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2">Work Experience Summary</label>
              <textarea
                name="experience"
                value={formData.experience}
                onChange={handleChange}
                placeholder="Software Intern at Tech Corp (3 months)..."
                rows={3}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-650 focus:outline-none focus:border-indigo-500/80 transition-all text-xs"
              />
            </div>
          </div>
        </div>

        {/* Submit Actions */}
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all disabled:opacity-50"
          >
            {isSaving ? "Saving to My Memory..." : "Save Profile Details"}
          </button>
          {saveSuccess && (
            <span className="text-emerald-400 text-xs font-bold flex items-center gap-1 animate-bounce">
              ✓ Successfully synced to My Memory!
            </span>
          )}
        </div>
      </form>
    </div>
  );
}

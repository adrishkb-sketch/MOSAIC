"use client";

import React, { useState, useEffect } from "react";
import { api, DocumentItem } from "@/lib/api";
import { FileText, Upload, Trash2, Edit3, Sparkles, Download, Save, FolderOpen } from "lucide-react";

interface DocumentManagerProps {
  email: string;
}

export default function DocumentManager({ email }: DocumentManagerProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Resume builder states
  const [resumeDraft, setResumeDraft] = useState<any>(null);
  const [isDrafting, setIsDrafting] = useState(false);
  const [editMode, setEditMode] = useState(false);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await api.getDocuments(email);
      setDocuments(docs);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [email]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    try {
      await api.uploadDocument(email, selectedFile);
      setSelectedFile(null);
      await fetchDocuments();
      alert("Resume uploaded and parsed successfully!");
    } catch (e) {
      console.error(e);
      alert("Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (confirm("Are you sure you want to delete this document?")) {
      try {
        await api.deleteDocument(id);
        setDocuments(documents.filter((d) => d.id !== id));
      } catch (e) {
        alert("Failed to delete document");
      }
    }
  };

  const handleDraftResume = async () => {
    setIsDrafting(true);
    try {
      const draft = await api.generateResumeDraft(email);
      setResumeDraft(draft);
      setEditMode(false);
    } catch (e) {
      console.error(e);
      alert("Failed to generate resume draft");
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSaveResume = async () => {
    if (!resumeDraft) return;
    try {
      await api.saveResumeDraft(email, resumeDraft);
      alert("Resume draft saved to My Memory successfully!");
      setResumeDraft(null);
    } catch (e) {
      console.error(e);
      alert("Failed to save resume draft");
    }
  };

  const downloadMarkdown = () => {
    if (!resumeDraft) return;
    const md = `
# ${resumeDraft.name}
**Email:** ${resumeDraft.email} | **Phone:** ${resumeDraft.phone}

## Professional Summary
${resumeDraft.summary}

## Skills
${resumeDraft.skills.join(", ")}

## Professional Experience
${resumeDraft.experience.map((exp: any) => `
### ${exp.role} @ ${exp.company}
*${exp.duration}*
${exp.details}
`).join("\n")}

## Education
${resumeDraft.education.map((edu: any) => `
### ${edu.degree}
*${edu.institution}* | GPA: ${edu.gpa} | *${edu.duration}*
`).join("\n")}
    `;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${resumeDraft.name.replace(/\s+/g, "_")}_Resume.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 flex flex-col p-8 overflow-y-auto max-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-indigo-200 to-violet-200 flex items-center gap-2">
          <FileText size={28} className="text-indigo-400" /> Document Center
        </h1>
        <p className="text-slate-700 dark:text-slate-300/80 text-sm mt-2">
          Upload resumes and application certificates privately. Extracted details populate your profile variables.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Column */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel rounded-3xl p-6 space-y-4">
            <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase border-b border-slate-300/50 dark:border-white/10 pb-2 flex items-center gap-2">
              <Upload size={16} className="text-indigo-400" /> Upload Document
            </h3>
            
            <div className="border border-dashed border-slate-400/50 dark:border-white/20 hover:border-indigo-500/50 transition-all rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer relative bg-white/40 dark:bg-black/20">
              <FileText size={32} className="mb-2 text-slate-500" />
              <span className="text-[10px] font-bold text-slate-350 uppercase tracking-wider block">
                {selectedFile ? selectedFile.name : "Select Resume File"}
              </span>
              <span className="text-[9px] text-slate-500 block mt-1">PDF, TXT, or DOCX formats</span>
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
            </div>

            {selectedFile && (
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-slate-900 dark:text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {isUploading ? "Processing Text..." : "Extract & Save Resume"}
              </button>
            )}
          </div>

          <div className="glass-panel rounded-3xl p-6 space-y-4">
            <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase border-b border-slate-300/50 dark:border-white/10 pb-2 flex items-center gap-2">
              <FolderOpen size={16} className="text-indigo-400" /> My Documents
            </h3>
            {isLoading ? (
              <div className="flex justify-center py-4">
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-indigo-500" />
              </div>
            ) : documents.length === 0 ? (
              <p className="text-slate-500 text-[10px] italic">No document uploads found.</p>
            ) : (
              <div className="space-y-3">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 rounded-xl bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-xs">
                    <div className="overflow-hidden pr-2">
                      <p className="text-slate-200 font-semibold truncate leading-tight">{doc.name}</p>
                      <span className="text-[9px] text-slate-500 font-medium font-mono">{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-rose-400 hover:text-rose-350 p-1 font-bold text-[10px]"
                      title="Delete document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Resume Generation/Preview Column */}
        <div className="lg:col-span-2 space-y-6">
          {!resumeDraft ? (
            <div className="glass-panel rounded-3xl p-8 flex flex-col items-center justify-center text-center">
              <Edit3 size={40} className="mb-4 text-slate-600" />
              <h3 className="text-slate-200 font-bold text-base">Draft a Professional Resume</h3>
              <p className="text-slate-600 dark:text-slate-400 text-xs mt-1 mb-6 max-w-md leading-relaxed">
                If you don't have a resume saved, MOSAIC can compile your basic education and skills details into a structured professional CV draft.
              </p>
              <button
                onClick={handleDraftResume}
                disabled={isDrafting}
                className="px-5 py-3 bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-600 hover:to-violet-600 text-slate-900 dark:text-white font-bold text-xs rounded-xl shadow-lg transition-all disabled:opacity-50"
              >
                {isDrafting ? "Compiling draft details..." : "Generate Resume Draft"}
              </button>
            </div>
          ) : (
            <div className="glass-panel rounded-3xl p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-300/50 dark:border-white/10 pb-4">
                <div>
                  <h3 className="text-slate-200 font-bold text-sm tracking-wide uppercase flex items-center gap-2">
                    <Sparkles size={16} className="text-indigo-400" /> Resume Assistant Draft
                  </h3>
                  <p className="text-[10px] text-slate-450 mt-0.5">Edit, export, and review the compiled content.</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={downloadMarkdown}
                    className="px-3 py-1.5 bg-slate-850 hover:bg-slate-200 dark:bg-slate-800 border border-slate-750 text-indigo-400 font-bold text-[10px] rounded-lg transition-all flex items-center gap-1.5"
                  >
                    <Download size={12} /> Export Markdown
                  </button>
                  <button
                    onClick={handleSaveResume}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-550 text-slate-900 dark:text-white font-bold text-[10px] rounded-lg transition-all flex items-center gap-1.5"
                  >
                    <Save size={12} /> Save to My Memory
                  </button>
                  <button
                    onClick={() => setResumeDraft(null)}
                    className="text-slate-500 hover:text-slate-350 text-xs font-bold px-2"
                  >
                    Discard
                  </button>
                </div>
              </div>

              {/* Editable Resume Draft Form */}
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400 tracking-wider mb-2">Name</label>
                    <input
                      type="text"
                      value={resumeDraft.name}
                      onChange={(e) => setResumeDraft({ ...resumeDraft, name: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-slate-200 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400 tracking-wider mb-2">Phone</label>
                    <input
                      type="text"
                      value={resumeDraft.phone}
                      onChange={(e) => setResumeDraft({ ...resumeDraft, phone: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-slate-200 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400 tracking-wider mb-2">Summary</label>
                  <textarea
                    value={resumeDraft.summary}
                    onChange={(e) => setResumeDraft({ ...resumeDraft, summary: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 rounded-xl bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-slate-200 text-xs leading-relaxed"
                  />
                </div>

                <div>
                  <label className="block text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400 tracking-wider mb-2">Skills (Comma-separated)</label>
                  <input
                    type="text"
                    value={resumeDraft.skills.join(", ")}
                    onChange={(e) => setResumeDraft({ ...resumeDraft, skills: e.target.value.split(",").map(s => s.trim()) })}
                    className="w-full px-3 py-2 rounded-xl bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 text-slate-200 text-xs"
                  />
                </div>

                <div className="space-y-3">
                  <span className="block text-[10px] uppercase font-bold text-slate-600 dark:text-slate-400 tracking-wider">Experience</span>
                  {resumeDraft.experience.map((exp: any, index: number) => (
                    <div key={index} className="bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 p-4 rounded-xl space-y-2">
                      <div className="grid grid-cols-2 gap-4">
                        <input
                          type="text"
                          value={exp.role}
                          onChange={(e) => {
                            const newExp = [...resumeDraft.experience];
                            newExp[index].role = e.target.value;
                            setResumeDraft({ ...resumeDraft, experience: newExp });
                          }}
                          className="bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 rounded-lg px-2 py-1 text-slate-200 text-[11px]"
                          placeholder="Role"
                        />
                        <input
                          type="text"
                          value={exp.company}
                          onChange={(e) => {
                            const newExp = [...resumeDraft.experience];
                            newExp[index].company = e.target.value;
                            setResumeDraft({ ...resumeDraft, experience: newExp });
                          }}
                          className="bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 rounded-lg px-2 py-1 text-slate-200 text-[11px]"
                          placeholder="Company"
                        />
                      </div>
                      <textarea
                        value={exp.details}
                        onChange={(e) => {
                          const newExp = [...resumeDraft.experience];
                          newExp[index].details = e.target.value;
                          setResumeDraft({ ...resumeDraft, experience: newExp });
                        }}
                        rows={2}
                        className="w-full bg-white/40 dark:bg-black/20 backdrop-blur-md border border-slate-300/50 dark:border-white/10 rounded-lg px-2 py-1 text-slate-200 text-[11px]"
                        placeholder="Details"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

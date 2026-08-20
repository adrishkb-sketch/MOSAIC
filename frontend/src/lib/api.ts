const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface SearchResultItem {
  title: string;
  url: string;
  description: string;
  price?: string;
  stipend?: string;
  deadline?: string;
  type?: "shopping" | "job" | "event" | "general";
  company?: string;
  location?: string;
}

export interface InteractiveOptionItem {
  id: string;
  title: string;
  description?: string;
  url?: string;
  selector?: string;
}

export interface ChatMessage {
  sender: "user" | "agent" | "system";
  text: string;
  timestamp: Date;
  results?: SearchResultItem[];
  options?: InteractiveOptionItem[];
  current_action?: string;
}

export interface MemoryItem {
  id: number;
  user_id: string;
  key: string;
  value: string;
  classification: string;
  source: string;
  usage_history: string;
  created_at: string;
  updated_at: string;
}

export interface MemoryWhyResponse {
  key: string;
  value: string;
  source: string;
  classification: string;
  created_at: string;
  updated_at: string;
  usage_history: Array<{
    task_id: string;
    task_description: string;
    website: string;
    timestamp: string;
  }>;
  shared_with_others: boolean;
  added_to_global_knowledge: boolean;
  explanation: string;
}

export interface ActivityItem {
  id: number;
  task_id: string;
  user_id: string;
  timestamp: string;
  request: string;
  interpreted_intent?: string;
  steps: string; // JSON string of steps
  information_used: string; // JSON string
  websites_visited: string; // JSON string
  actions_performed: string; // JSON string
  approval_requests: string; // JSON string
  final_action?: string;
  result?: string;
  status: "thinking" | "asking" | "browsing" | "waiting_approval" | "completed" | "failed" | "cancelled";
  updated_at: string;
}

export interface DocumentItem {
  id: number;
  user_id: string;
  name: string;
  file_type: string;
  extracted_text?: string;
  metadata_json: string;
  created_at: string;
}

export interface ActionPlanItem {
  id: number;
  task_id: string;
  user_id: string;
  goal: string;
  website: string;
  actions: string; // JSON string
  information_to_be_sent: string; // JSON string
  risk_level: "READ_ONLY" | "LOW_RISK" | "CONSEQUENTIAL" | "HIGH_RISK";
  approval_required: boolean;
  approval_status: "pending" | "approved" | "rejected";
  final_action?: string;
  created_at: string;
}

export interface SharedWebsiteItem {
  id: number;
  domain: string;
  name: string;
  workflows: string;
  commands: string;
  success_rate: number;
  uses_count: number;
  fallback_strategies: string;
  last_validated: string;
  last_updated: string;
}

// Fetch Wrapper
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Memories
  getMemories: (email: string) => 
    request<MemoryItem[]>(`/memory/items?email=${encodeURIComponent(email)}`),
    
  addMemory: (email: string, item: { key: string; value: string; classification: string; source: string }) =>
    request<MemoryItem>(`/memory/items?email=${encodeURIComponent(email)}`, {
      method: "POST",
      body: JSON.stringify(item),
    }),
    
  updateMemory: (id: number, item: { value?: string; classification?: string; source?: string }) =>
    request<MemoryItem>(`/memory/items/${id}`, {
      method: "PUT",
      body: JSON.stringify(item),
    }),
    
  deleteMemory: (id: number) =>
    request<{ status: string; message: string }>(`/memory/items/${id}`, {
      method: "DELETE",
    }),
    
  clearMemories: (email: string) =>
    request<{ status: string; message: string }>(`/memory/items?email=${encodeURIComponent(email)}`, {
      method: "DELETE",
    }),
    
  getMemoryWhy: (id: number) =>
    request<MemoryWhyResponse>(`/memory/items/${id}/why`),

  // Activities
  getActivities: (email: string) =>
    request<ActivityItem[]>(`/activity/logs?email=${encodeURIComponent(email)}`),
    
  getActivity: (taskId: string) =>
    request<ActivityItem>(`/activity/logs/${taskId}`),

  // Action Plans & Approvals
  getActionPlan: (taskId: string) =>
    request<ActionPlanItem>(`/agent/action-plan/${taskId}`),
    
  approveActionPlan: (taskId: string, approved: boolean) =>
    request<{ status: string; message: string }>(`/agent/action-plan/${taskId}/approve`, {
      method: "POST",
      body: JSON.stringify({ approved }),
    }),

  // Learned Websites
  getLearnedWebsites: () =>
    request<SharedWebsiteItem[]>("/learned-websites/items"),

  // Documents
  getDocuments: (email: string) =>
    request<DocumentItem[]>(`/documents/items?email=${encodeURIComponent(email)}`),
    
  uploadDocument: async (email: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await fetch(`${API_BASE_URL}/documents/upload?email=${encodeURIComponent(email)}`, {
      method: "POST",
      body: formData,
    });
    
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Upload failed");
    }
    
    return response.json() as Promise<DocumentItem>;
  },
  
  deleteDocument: (id: number) =>
    request<{ status: string; message: string }>(`/documents/items/${id}`, {
      method: "DELETE",
    }),

  // Agent Chat Interaction
  chat: (email: string, message: string, taskId?: string) =>
    request<{
      task_id: string;
      status: string;
      response: string;
      clarification_needed: boolean;
      action_plan_required: boolean;
      action_plan?: any;
      browser_active: boolean;
      browser_url?: string;
      screenshot?: string;
      results?: SearchResultItem[];
      options?: InteractiveOptionItem[];
      current_action?: string;
    }>("/agent/chat", {
      method: "POST",
      body: JSON.stringify({ email, message, task_id: taskId }),
    }),
    
  // Resume Generation
  generateResumeDraft: (email: string) =>
    request<any>(`/documents/resume-draft?email=${encodeURIComponent(email)}`),
    
  saveResumeDraft: (email: string, resumeData: any) =>
    request<{ status: string; message: string }>(`/documents/resume-draft?email=${encodeURIComponent(email)}`, {
      method: "POST",
      body: JSON.stringify(resumeData),
    }),
};

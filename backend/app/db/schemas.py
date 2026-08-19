from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Memory Schemas ---
class MemoryBase(BaseModel):
    key: str
    value: str
    classification: str
    source: str
    usage_history: Optional[str] = "[]"

class MemoryCreate(MemoryBase):
    pass

class MemoryUpdate(BaseModel):
    value: Optional[str] = None
    classification: Optional[str] = None
    source: Optional[str] = None

class MemoryResponse(MemoryBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Document Schemas ---
class DocumentResponse(BaseModel):
    id: int
    user_id: str
    name: str
    file_type: str
    extracted_text: Optional[str] = None
    metadata_json: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Activity Schemas ---
class ActivityBase(BaseModel):
    task_id: str
    user_id: str
    request: str
    interpreted_intent: Optional[str] = None
    steps: Optional[str] = "[]"
    information_used: Optional[str] = "[]"
    websites_visited: Optional[str] = "[]"
    actions_performed: Optional[str] = "[]"
    approval_requests: Optional[str] = "[]"
    final_action: Optional[str] = None
    result: Optional[str] = None
    status: str = "thinking"

class ActivityResponse(ActivityBase):
    id: int
    timestamp: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Action Plan Schemas ---
class ActionItem(BaseModel):
    action_type: str  # click, fill, navigate, extract, purchase, submit
    description: str
    selector: Optional[str] = None
    value: Optional[str] = None

class ActionPlanBase(BaseModel):
    task_id: str
    goal: str
    website: str
    actions: str  # JSON string of List[ActionItem]
    information_to_be_sent: str  # JSON string of Dict[str, Any]
    risk_level: str
    approval_required: bool = True
    approval_status: str = "pending"
    final_action: Optional[str] = None

class ActionPlanCreate(ActionPlanBase):
    pass

class ActionPlanApproval(BaseModel):
    approved: bool

class ActionPlanResponse(ActionPlanBase):
    id: int
    user_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Shared Website Schemas ---
class SharedWebsiteBase(BaseModel):
    domain: str
    name: str
    workflows: str  # JSON string
    commands: str  # JSON string
    success_rate: float
    uses_count: int
    fallback_strategies: str  # JSON string

class SharedWebsiteResponse(SharedWebsiteBase):
    id: int
    last_validated: datetime
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Chat/Agent Schemas ---
class ChatMessage(BaseModel):
    sender: str  # user, agent, system
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatRequest(BaseModel):
    email: str
    message: str
    task_id: Optional[str] = None

class ChatResponse(BaseModel):
    task_id: str
    status: str
    response: str
    clarification_needed: bool
    action_plan_required: bool
    action_plan: Optional[Dict[str, Any]] = None
    browser_active: bool = False
    browser_url: Optional[str] = None
    screenshot: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None

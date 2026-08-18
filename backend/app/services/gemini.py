import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.core.config import settings

# --- Pydantic Schemas for Gemini Structured Outputs ---

class TaskIntent(BaseModel):
    intent_type: str = Field(description="One of: research, comparison, shopping, booking, application, registration, communication, document_preparation, other")
    description: str = Field(description="Short explanation of what the user wants to achieve")
    required_fields: List[str] = Field(description="Keys/fields needed to complete this task (e.g. 'skills', 'budget', 'location')")

class MissingInformation(BaseModel):
    missing_fields: List[str] = Field(description="List of fields needed for this task that are not in the profile or request")
    questions: List[str] = Field(description="Clarifying questions to ask the user (concise and friendly)")

class TaskPlanStep(BaseModel):
    step_number: int
    description: str
    tool: str = Field(description="Tool to use: web_research, web_interact, user_memory, none")
    details: str

class TaskPlan(BaseModel):
    goal: str = Field(description="Overall goal of the task")
    steps: List[TaskPlanStep] = Field(description="Sequential steps to execute")

class FormFieldMapping(BaseModel):
    form_field_label: str = Field(description="The visible label or placeholder of the input field on the page")
    form_field_name: str = Field(description="The name or id attribute of the input element")
    user_profile_key: str = Field(description="Semantic path in user profile, e.g., 'user.name', 'user.education.institution', or 'null' if not found")
    value: Optional[str] = Field(description="The actual value to fill, derived from user profile, or null if missing")
    reason: str = Field(description="Reason for this mapping")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")

class FormMappingResult(BaseModel):
    mappings: List[FormFieldMapping]

class ActionItem(BaseModel):
    action_type: str = Field(description="click, fill, navigate, extract, purchase, submit")
    description: str = Field(description="Human readable description of the action")
    selector: Optional[str] = Field(description="CSS selector or ref if applicable")
    value: Optional[str] = Field(description="Value to fill if action is fill")

class ActionPlanSchema(BaseModel):
    goal: str
    website: str
    actions: List[ActionItem]
    information_to_be_sent: Dict[str, Any] = Field(description="Private user data that will be shared with the website during this plan")
    risk_level: str = Field(description="READ_ONLY, LOW_RISK, CONSEQUENTIAL, HIGH_RISK")
    approval_required: bool
    final_action: Optional[str] = Field(description="The final consequential action description, if any")

class UserMemoryCandidate(BaseModel):
    key: str = Field(description="Camel_case key name, e.g. 'preferredLocation', 'shoppingBudget'")
    value: str = Field(description="Value of the memory")
    classification: str = Field(description="PRIVATE_USER_DATA, SENSITIVE_USER_DATA, EXPLICIT_PREFERENCE, INFERRED_PREFERENCE")
    source: str = Field(description="explicit or inferred")
    reason: str = Field(description="Why this should be saved as a memory")

class UserMemoryResult(BaseModel):
    candidates: List[UserMemoryCandidate]

class ResumeDraftResult(BaseModel):
    name: str
    email: str
    phone: str
    education: List[Dict[str, Any]]
    experience: List[Dict[str, Any]]
    skills: List[str]
    projects: List[Dict[str, Any]]
    summary: str

# --- Gemini Service Provider Class ---

class GeminiService:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> genai.Client:
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please supply it in backend/.env to use Gemini features."
            )
        if self._client is None:
            # We initialize client with settings.GEMINI_API_KEY
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _call_model(self, contents: str, response_schema: Any, model: str = "gemini-2.5-flash") -> Any:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1
                )
            )
            return response.parsed
        except Exception as e:
            # Re-raise with a clear message
            raise RuntimeError(f"Gemini API Call Failed: {str(e)}")

    def classify_intent(self, user_request: str) -> TaskIntent:
        prompt = f"""
        Classify the intent of the following user request for a browser agent:
        Request: "{user_request}"
        """
        return self._call_model(prompt, TaskIntent)

    def identify_missing_info(self, user_request: str, user_profile: Dict[str, Any]) -> MissingInformation:
        prompt = f"""
        Given the user request: "{user_request}"
        And the current known user profile: {json.dumps(user_profile)}
        
        Identify any missing information required to execute this request and generate clarification questions.
        """
        return self._call_model(prompt, MissingInformation)

    def generate_task_plan(self, user_request: str, user_profile: Dict[str, Any]) -> TaskPlan:
        prompt = f"""
        Create a step-by-step task plan to achieve this request: "{user_request}"
        Known user details: {json.dumps(user_profile)}
        """
        return self._call_model(prompt, TaskPlan)

    def map_form_fields(self, form_fields: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[FormFieldMapping]:
        prompt = f"""
        Map these webpage form fields to the user profile.
        Form fields: {json.dumps(form_fields)}
        User profile: {json.dumps(user_profile)}
        
        For each field, determine if there is a match. Provide the path and actual value from profile if it exists.
        """
        result: FormMappingResult = self._call_model(prompt, FormMappingResult)
        return result.mappings

    def generate_action_plan(self, task: str, url: str, page_snapshot: str, user_profile: Dict[str, Any]) -> ActionPlanSchema:
        prompt = f"""
        Task: "{task}"
        Current website URL: {url}
        Accessibility tree snapshot:
        {page_snapshot}
        
        User Profile: {json.dumps(user_profile)}
        
        Create a structured ActionPlan detailing the browser clicks/fills needed.
        Examine the security and risk of this action. If it is a submission, booking, email draft or purchase, it must be CONSEQUENTIAL and require approval.
        """
        return self._call_model(prompt, ActionPlanSchema)

    def extract_memories(self, conversation_history: List[Dict[str, Any]]) -> List[UserMemoryCandidate]:
        prompt = f"""
        Analyze the conversation history and extract any user preferences, career profile elements, or contact info that should be saved to the private user memory.
        History: {json.dumps(conversation_history)}
        """
        result: UserMemoryResult = self._call_model(prompt, UserMemoryResult)
        return result.candidates

    def generate_resume_draft(self, user_profile: Dict[str, Any]) -> ResumeDraftResult:
        prompt = f"""
        Generate a complete professional resume/CV draft based on the user's profile information:
        {json.dumps(user_profile)}
        
        Fill in realistic professional summaries and structure it cleanly.
        """
        return self._call_model(prompt, ResumeDraftResult)

gemini_service = GeminiService()

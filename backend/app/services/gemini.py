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

class ProfileFieldUsage(BaseModel):
    key: str
    value: str

class ActionPlanSchema(BaseModel):
    goal: str
    website: str
    actions: List[ActionItem]
    information_to_be_sent: List[ProfileFieldUsage] = Field(description="Private user data that will be shared with the website during this plan")
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

class ResumeDraftEducation(BaseModel):
    institution: str
    degree: str
    year: str

class ResumeDraftExperience(BaseModel):
    company: str
    role: str
    duration: str

class ResumeDraftProject(BaseModel):
    title: str
    description: str

class ResumeDraftResult(BaseModel):
    name: str
    email: str
    phone: str
    education: List[ResumeDraftEducation]
    experience: List[ResumeDraftExperience]
    skills: List[str]
    projects: List[ResumeDraftProject]
    summary: str

class TableRow(BaseModel):
    cells: List[str]

class BrowserNextAction(BaseModel):
    thought: str = Field(description="The thinking process, analyzing the page state, links, or fields relative to the goal.")
    action_type: str = Field(description="One of: click, fill, navigate, wait, ask_user_otp, submit_form_approval, complete")
    selector: Optional[str] = Field(None, description="CSS selector or element selector for click/fill")
    value: Optional[str] = Field(None, description="The value to fill if action_type is fill")
    url: Optional[str] = Field(None, description="The target URL to navigate to if action_type is navigate")
    question: Optional[str] = Field(None, description="The question or OTP request message to return to the user if action_type is ask_user_otp")
    table_headers: Optional[List[str]] = Field(None, description="Headers for the comparison table")
    table_rows: Optional[List[TableRow]] = Field(None, description="Rows for the comparison table (each row contains a cells list matching headers)")
    final_summary: Optional[str] = Field(None, description="Final summary text if task is complete")

# --- Gemini Service Provider Class ---

class GeminiService:
    def __init__(self):
        self.api_keys = []
        self.current_key_idx = 0
        self._clients = {}
        self.reload_keys()

    def reload_keys(self):
        raw_key = settings.GEMINI_API_KEY
        if raw_key:
            self.api_keys = [k.strip() for k in raw_key.split(",") if k.strip()]
        else:
            self.api_keys = []

    def rotate_key(self) -> bool:
        """Rotates to the next key. Returns True if successfully rotated to a new key."""
        if not self.api_keys:
            return False
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        print(f"Rotating to Gemini API Key at index {self.current_key_idx}")
        return True

    @property
    def client(self) -> genai.Client:
        self.reload_keys()
        if not self.api_keys:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please supply it in backend/.env to use Gemini features."
            )
        key = self.api_keys[self.current_key_idx]
        if key not in self._clients:
            self._clients[key] = genai.Client(api_key=key)
        return self._clients[key]

    def is_configured(self) -> bool:
        self.reload_keys()
        return len(self.api_keys) > 0

    def generate_content(self, model: str, contents: Any, config: Any = None) -> Any:
        self.reload_keys()
        if not self.api_keys:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please supply it in backend/.env to use Gemini features."
            )
        attempts = 0
        max_attempts = len(self.api_keys)
        last_error = None
        while attempts < max_attempts:
            try:
                cl = self.client
                return cl.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            except Exception as e:
                print(f"Gemini generate_content failed with key index {self.current_key_idx}: {e}")
                last_error = e
                self.rotate_key()
                attempts += 1
        raise RuntimeError(f"All Gemini API Keys failed. Last error: {str(last_error)}")

    def _call_model(self, contents: str, response_schema: Any, model: str = "gemini-2.5-flash") -> Any:
        self.reload_keys()
        if not self.api_keys:
            raise RuntimeError("No Gemini API keys configured.")
        attempts = 0
        max_attempts = len(self.api_keys)
        last_error = None
        while attempts < max_attempts:
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
                print(f"Gemini model call failed with key index {self.current_key_idx}: {e}")
                last_error = e
                self.rotate_key()
                attempts += 1
        raise RuntimeError(f"All Gemini API Keys failed. Last error: {str(last_error)}")

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

    def determine_next_browser_action(
        self,
        goal: str,
        current_url: Optional[str],
        page_snapshot: str,
        user_profile: Dict[str, Any],
        execution_history: List[Dict[str, Any]]
    ) -> BrowserNextAction:
        prompt = f"""
        You are driving a browser agent to achieve this user goal: "{goal}"
        
        Current URL: {current_url}
        Accessibility tree snapshot of the page:
        {page_snapshot}
        
        User's Private Profile: {json.dumps(user_profile)}
        Execution History so far: {json.dumps(execution_history)}
        
        Analyze the current page state, compare it with the goal, and decide the NEXT action.
        Guidelines:
        0. FIRST-STEP SITE ANALYSIS: Analyze the page state at the very beginning of the site navigation. Check if a cookie banner, sign-in block, or sign-up modal is blocking the page or is required to proceed. If so, handle it first (e.g. click accept, or perform sign-in/sign-up using profile credentials if present). Do not skip this step.
        1. If you need to search or research first, navigate to a real, relevant website or search portal (e.g. Google, LinkedIn, Amazon, etc.).
        2. If you see search results or list options, analyze them, select the best ones, and you can prepare a structured table (using table_headers and table_data) to compare them for the user.
        3. If you need to click a link to navigate to a target detail page, use 'click' or 'navigate'.
        4. If you need to fill forms, map fields from the User Profile.
        5. If you reach a payment checkout page, safety rules require you to stop and ask for manual payment.
        6. If you need a verification code, OTP, or user input, set action_type to 'ask_user_otp' and define the question.
        7. If you are ready to perform a consequential action (submitting a form, booking a ticket, registering), set action_type to 'submit_form_approval' and describe it.
        8. If you have successfully achieved the goal, set action_type to 'complete' and provide a final_summary.
        """
        return self._call_model(prompt, BrowserNextAction)

gemini_service = GeminiService()

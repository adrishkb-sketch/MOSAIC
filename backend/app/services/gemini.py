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

class InteractiveOption(BaseModel):
    id: str = Field(description="Short identifier or index like '1', '2', '3'")
    title: str = Field(description="Option title, e.g. 'Byomkesh Bakshi Samagra' or 'Option 1: Hardcover Edition'")
    description: Optional[str] = Field(None, description="Short detail, author, price, rating, or subtitle")
    url: Optional[str] = Field(None, description="Direct URL if navigating to a separate link")
    selector: Optional[str] = Field(None, description="CSS selector on the current page to click if chosen")

class VerifiedCatalogItem(BaseModel):
    id: str = Field(description="Option or item sequence ID ('1', '2', '3')")
    title: str = Field(description="Real, authentic product/item name and model (e.g. 'HP Victus Intel Core i5 13th Gen RTX 4050' or 'Byomkesh Bakshi Samagra'). Strictly NEVER include UI text like 'Add to Compare', 'Sponsored', or button labels.")
    price: Optional[str] = Field(None, description="Clean price with currency symbol, e.g. '₹68,990'")
    specs_or_details: Optional[str] = Field(None, description="Detailed specifications, author, ratings, or highlights (e.g. '16GB RAM | 512GB SSD | 6GB RTX 4050 | 144Hz IPS')")
    url: Optional[str] = Field(None, description="Direct URL to product or listing page")
    selector: Optional[str] = Field(None, description="CSS selector to click or interact with this item on the page")

class VerifiedCatalogResponse(BaseModel):
    items: List[VerifiedCatalogItem] = Field(description="List of verified authentic product/content items matching the user request.")
    summary: str = Field(description="Concise, helpful summary describing the verified choices for the user.")

class ProfileEnrichmentCheck(BaseModel):
    should_ask_enrichment: bool = Field(description="True if asking the user to confirm, update, or expand their profile/skills/preferences (e.g. adding more skills for internships, confirming budget/specs for shopping, location for jobs) would significantly improve the task outcome before searching.")
    question_to_user: str = Field(description="Friendly, conversational question asking the user if they'd like to add more specific skills, preferences, or details, or proceed with what is currently saved in private memory.")
    options: List[InteractiveOption] = Field(description="2-3 options: Option 1: 'Proceed with current profile (e.g. skills)', Option 2: 'Add more skills / preferences'.")

class TableRow(BaseModel):
    cells: List[str]

class BrowserNextAction(BaseModel):
    thought: str = Field(description="The thinking process, analyzing the page state, links, or fields relative to the goal.")
    action_type: str = Field(description="One of: click, fill, navigate, wait, ask_user_choice, ask_user_otp, ask_user_login, ask_user_signup, fill_address, submit_form_approval, payment_boundary, complete")
    selector: Optional[str] = Field(None, description="CSS selector or element selector for click/fill")
    click_text: Optional[str] = Field(None, description="Visible text of the button, link, or tab to click (e.g., 'Price -- Low to High', 'Cheapest', 'Buy Now', 'Proceed to Checkout', 'Deliver Here')")
    value: Optional[str] = Field(None, description="The value to fill if action_type is fill")
    press_enter: Optional[bool] = Field(False, description="Whether to press Enter after typing into input field (e.g. for search inputs)")
    url: Optional[str] = Field(None, description="The target URL to navigate to if action_type is navigate")
    question: Optional[str] = Field(None, description="The question, clarification, login credential request, or OTP request message to return to the user")
    options: Optional[List[InteractiveOption]] = Field(None, description="List of selectable options/items for the user to choose from if action_type is ask_user_choice. Must have real product names, NEVER 'Add to Compare'.")
    table_headers: Optional[List[str]] = Field(None, description="Headers for the comparison table")
    table_rows: Optional[List[TableRow]] = Field(None, description="Rows for the comparison table (each row contains a cells list matching headers)")
    final_summary: Optional[str] = Field(None, description="Final summary text if task is complete")


class BroadQueryRecommendation(BaseModel):
    is_broad_query: bool = Field(description="True if the user request is broad, exploratory, or recommendations-seeking (e.g. 'buy a good bengali book', 'suggest coding laptops') rather than an exact specific command with all parameters.")
    recommendations_summary: str = Field(description="Friendly explanation and helpful guidance/questions for the user.")
    suggested_options: List[InteractiveOption] = Field(description="3-5 specific recommendations, genres, top picks, or filters for the user to pick from. Must match user's explicit tier or preferences.")

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
            keys = [k.strip() for k in raw_key.split(",") if k.strip()]
            # Filter out obvious placeholder values like 'your_gemini_api_key_here'
            self.api_keys = [k for k in keys if not k.lower().startswith("your_")]
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

    def analyze_query_or_recommend(self, user_request: str, user_profile: Dict[str, Any]) -> BroadQueryRecommendation:
        prompt = f"""
        You are MOSAIC, an intelligent personal browser agent.
        The user said: "{user_request}"
        Known user profile: {json.dumps(user_profile)}

        Analyze if this is a broad, discovery, or recommendation-seeking request (e.g. "buy a good bengali book", "suggest laptops for college", "find tech events in Kolkata", "recommend sci-fi books").
        
        CRITICAL RULES:
        1. If the user specified a tier, budget, or specific category (e.g. "mid range gaming laptops", "laptops under 70k", "RTX 4060 gaming laptops"):
           - MUST PRESERVE the exact tier ("mid range", "budget", etc.). NEVER change or downgrade "mid range" to "entry level" or "basic".
           - Provide 3-4 top recommended laptop models or specific sub-options in THAT EXACT tier (e.g., Lenovo LOQ RTX 4050, Acer Nitro V RTX 4050, ASUS TUF A15).
        2. If it IS a broad request:
           - Set is_broad_query to true.
           - In recommendations_summary, provide a friendly, helpful conversational response with expert curated context, and ask what they prefer.
           - In suggested_options, give 3-5 specific top-rated recommendations (with id, title, description matching the user's criteria).
        3. If the user already specified a precise item/action (e.g. "buy Byomkesh Bakshi Samagra", "search for lenovo ideapad 3 on amazon", "apply for python intern at Google"):
           - Set is_broad_query to false.
           - suggested_options can be empty.
        """
        return self._call_model(prompt, BroadQueryRecommendation)

    def verify_and_clean_catalog_items(
        self,
        user_query: str,
        page_title: str,
        current_url: str,
        raw_items: List[Dict[str, Any]],
        page_snapshot: str = ""
    ) -> VerifiedCatalogResponse:
        prompt = f"""
        You are MOSAIC's strict AI Verification & Extraction Engine.
        Your job is to examine raw scraped items and the live website page state, verify every product/item, and remove any scraping junk or UI artifacts before anything is shown to the user.

        User Request / Query: "{user_query}"
        Current Website: {current_url} (Page Title: {page_title})
        Raw Scraped Items from Webcmd:
        {json.dumps(raw_items)}

        Page Accessibility / Text Snippet:
        {page_snapshot[:4000]}

        CRITICAL VERIFICATION RULES:
        1. AUTHENTIC PRODUCT NAMES: Each item's 'title' MUST be the genuine, full product/model name (e.g. "Acer Nitro V 15 Intel Core i5 13th Gen (16GB/512GB SSD/RTX 4050)", "Lenovo LOQ Core i5 12th Gen RTX 3050", "ASUS TUF Gaming A15", "Byomkesh Bakshi Samagra").
        2. STRICT JUNK BAN: NEVER EVER return UI action labels, button texts, or promotional banners as product titles. Strictly discard or fix:
           - "Add to Compare", "Compare", "Add to wishlist", "Sponsored", "Bank Offer", "Free delivery", "Special Price", "HOT DEALS", "Top Discount", "Ratings & Reviews", "4.2 ★", "Buy Now", "Add to Cart", "Sign in", "Explore Plus".
        3. USER INTENT & TIER FIDELITY: Ensure the selected items match the user's specific request and tier (e.g. if the user specified 'mid range gaming laptops', select gaming laptops in the mid-range tier like RTX 4050 / RTX 4060, NOT entry-level or non-gaming machines).
        4. ACCURATE DETAILS: In 'price', provide the actual formatted price (e.g. '₹69,990'). In 'specs_or_details', include key specs like processor, graphics card, RAM, SSD, or rating.
        5. PRESERVE SELECTOR & URL: Retain the selector or URL from the matching raw item so the browser agent can click or navigate to it.
        6. Provide at most 4-5 top verified items and a friendly, concise summary.
        """
        return self._call_model(prompt, VerifiedCatalogResponse)

    def check_profile_enrichment(self, user_request: str, user_profile: Dict[str, Any]) -> ProfileEnrichmentCheck:
        prompt = f"""
        You are MOSAIC, an intelligent personal browser agent with private scoped memory.
        User Request: "{user_request}"
        Current User Profile in Memory: {json.dumps(user_profile)}

        Analyze if we should proactively ask the user to confirm, update, or expand their profile/skills/preferences before proceeding with this task.
        
        Guidelines:
        1. If applying for internships/jobs and the profile has skills (e.g. "Python, React"):
           - Set should_ask_enrichment to true.
           - In question_to_user, say: "I see your saved skills are **{user_profile.get('skills', '')}**. Would you like to add any more skills, tech stacks, or domains (e.g. backend, ML, Docker) before I search, or should I proceed with these?"
           - In options, provide Option 1: "Proceed with saved skills ({user_profile.get('skills', '')})" and Option 2: "Add more skills or preferences".
        2. If shopping or comparing items and user might have budget/brand/spec preferences:
           - If useful, ask if they want to specify any additional constraints or proceed.
        3. If the user already provided specific criteria or explicitly said to proceed, set should_ask_enrichment to false.
        """
        return self._call_model(prompt, ProfileEnrichmentCheck)

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
        execution_history: List[Dict[str, Any]],
        user_instruction: Optional[str] = None
    ) -> BrowserNextAction:
        prompt = f"""
        You are MOSAIC, an intelligent personal browser agent driving a live browser session.
        Goal: "{goal}"
        Latest User Instruction: "{user_instruction or goal}"
        Current Page URL: {current_url}

        Accessibility Snapshot / DOM elements:
        {page_snapshot}

        User Profile / Preferences:
        {json.dumps(user_profile)}

        Execution History so far:
        {json.dumps(execution_history)}

        Analyze the current page state, compare it with the goal and latest instruction, and determine the exact NEXT logical action to execute on this website.

        Decision Guidelines:
        1. POPUPS / COOKIES / MODALS: If a popup, overlay, location prompt, or cookie consent is blocking the page, set action_type to 'click' on the close/accept button.
        2. SORTING & FILTERING: If the user wants the cheapest, lowest price, highest rating, or a specific brand/filter:
           - Look for sort tabs/dropdowns/links (e.g. 'Price -- Low to High', 'Price: Low to High', 'Sort By', 'Filters', 'Customer Rating', 'Low to High').
           - Set action_type to 'click' with the appropriate selector or click_text.
        3. SEARCHING WITHIN PORTAL: If the user wants to search for a new item or keyword on this portal:
           - Locate the search input (e.g. input[title*="Search"], input[name="q"], #twotabsearchtextbox, input[placeholder*="Search"]).
           - Set action_type to 'fill', set selector, set value to the search term, and set press_enter=True.
        4. CATALOG / SEARCH RESULTS / CHOICES: If on a catalog/search results page and items are visible:
           - If the user needs to select an item, extract the top 3-5 visible items into the 'options' list (with id, title, price/details, and selector or url).
           - Set action_type to 'ask_user_choice' and explain the choices concisely.
        5. PRODUCT DETAILS & CART / CHECKOUT TRAVEL: If on a product page or cart view and the goal is to buy/purchase/apply:
           - Set action_type to 'click' on 'Buy Now', 'Add to Cart', 'Proceed to Checkout', 'Place Order', 'Go to Cart', or 'Deliver to this address'.
           - Keep travelling automatically through checkout steps!
        6. LOGIN / SIGNUP CREDENTIALS: If the page requires login or signup:
           - If phone or email is in profile, fill it. If user credentials (password/phone/signup) are needed, set action_type to 'ask_user_login' or 'ask_user_signup' with a clear prompt for the user.
        7. VERIFICATION / OTP: If the page asks for an SMS or email OTP:
           - Set action_type to 'ask_user_otp', selector to OTP input, and question to "Please enter the OTP verification code sent to your phone/email:".
        8. ADDRESS & FORM FILLING: If on an address, shipping, or job application form:
           - Map user profile fields (name, phone, address, pincode, city, skills) and set action_type to 'fill'.
        9. PAYMENT SAFETY BOUNDARY: If checkout reaches payment method selection, card number, CVV, UPI ID, or final pay button:
           - STRICT SAFETY RULE: set action_type to 'payment_boundary' and explain that manual payment is required inside the browser viewport.
        10. SUBMISSION CONFIRMATION: If ready to submit a non-payment consequential action, set action_type to 'submit_form_approval'.
        11. COMPLETION: If the user's instruction or task is fully satisfied, set action_type to 'complete' with final_summary.
        """
        return self._call_model(prompt, BrowserNextAction)

gemini_service = GeminiService()


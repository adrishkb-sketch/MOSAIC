from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    risk_level: str  # READ_ONLY, LOW_RISK, CONSEQUENTIAL, HIGH_RISK
    requires_approval: bool
    allowed_contexts: List[str]

class ToolRouter:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register_tool(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def _register_default_tools(self) -> None:
        # 1. Read-only/low-risk research and browsing
        self.register_tool(ToolDefinition(
            name="web_research",
            description="Perform read-only web search and open pages to fetch information",
            risk_level="READ_ONLY",
            requires_approval=False,
            allowed_contexts=["any"]
        ))
        self.register_tool(ToolDefinition(
            name="web_extract",
            description="Extract text, elements, or structured tables from the active page",
            risk_level="READ_ONLY",
            requires_approval=False,
            allowed_contexts=["any"]
        ))

        # 2. Local memory tools
        self.register_tool(ToolDefinition(
            name="search_user_memory",
            description="Query the isolated private memory to retrieve relevant profile facts",
            risk_level="READ_ONLY",
            requires_approval=False,
            allowed_contexts=["any"]
        ))
        self.register_tool(ToolDefinition(
            name="save_user_memory",
            description="Explicitly save a key-value fact into the user memory namespace",
            risk_level="LOW_RISK",
            requires_approval=False,
            allowed_contexts=["any"]
        ))

        # 3. Interactivity tools
        self.register_tool(ToolDefinition(
            name="web_interact",
            description="Perform interactive actions like clicking links, navigating pages, or scrolling",
            risk_level="LOW_RISK",
            requires_approval=False,
            allowed_contexts=["any"]
        ))
        self.register_tool(ToolDefinition(
            name="webcmd_execute",
            description="Execute a learned Webcmd CLI command to accelerate known site automation",
            risk_level="LOW_RISK",
            requires_approval=False,
            allowed_contexts=["any"]
        ))

        # 4. Consequential submission tools (require approval)
        self.register_tool(ToolDefinition(
            name="prepare_application",
            description="Autofill forms and prepare job/internship applications for final submission",
            risk_level="CONSEQUENTIAL",
            requires_approval=True,
            allowed_contexts=["application"]
        ))
        self.register_tool(ToolDefinition(
            name="prepare_checkout",
            description="Compare products, add item to cart, and fill shipping details to prepare purchase",
            risk_level="CONSEQUENTIAL",
            requires_approval=True,
            allowed_contexts=["shopping"]
        ))
        self.register_tool(ToolDefinition(
            name="prepare_registration",
            description="Fill details for event or hackathon registration forms",
            risk_level="CONSEQUENTIAL",
            requires_approval=True,
            allowed_contexts=["registration"]
        ))

        # 5. High-risk financial/auth tools (block automation)
        self.register_tool(ToolDefinition(
            name="execute_payment",
            description="Perform credit card entries, bank pins, UPI, or final purchase payments",
            risk_level="HIGH_RISK",
            requires_approval=True,
            allowed_contexts=["shopping"]
        ))
        self.register_tool(ToolDefinition(
            name="submit_application",
            description="Perform the final consequential submit button click on job portal",
            risk_level="CONSEQUENTIAL",
            requires_approval=True,
            allowed_contexts=["application"]
        ))

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def validate_action(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Policy Engine: checks the risk level of the tool and enforces human-in-the-loop validation rules.
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "allowed": False,
                "reason": f"Tool '{tool_name}' is not registered or allowed under system policy.",
                "requires_approval": False
            }

        # Hard-coded safety boundary: Block automation of payments
        if tool.risk_level == "HIGH_RISK" or tool_name == "execute_payment":
            return {
                "allowed": False,
                "reason": "HIGH RISK: Payments and credentials entries must be done manually in the viewport. Automation is blocked.",
                "requires_approval": False,
                "manual_action_required": True
            }

        # Check approval requirement
        if tool.requires_approval:
            return {
                "allowed": True,
                "reason": f"Action requires explicit user approval due to risk level '{tool.risk_level}'.",
                "requires_approval": True
            }

        # Safe for automatic execution
        return {
            "allowed": True,
            "reason": "Safe for automatic execution.",
            "requires_approval": False
        }

tool_router = ToolRouter()

import json
import uuid
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models import UserActivity, ActionPlan, UserMemory
from app.services.gemini import gemini_service, TaskIntent, TaskPlan, MissingInformation, ActionPlanSchema
from app.services.webcmd import webcmd_client
from app.services.memory import memory_service
from app.services.router import tool_router

# In-memory store for active task sessions
# Maps task_id -> { "session_id": str, "email": str, "request": str, "status": str, "current_url": str }
active_sessions: Dict[str, Dict[str, Any]] = {}

class AgentOrchestrator:
    def chat(
        self,
        db: Session,
        email: str,
        message: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main agent loop entry point. Processes conversational inputs,
        manages browser execution, and triggers approval checkpoints.
        """
        # 1. Initialize or load task session
        if not task_id:
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            active_sessions[task_id] = {
                "session_id": None,
                "email": email,
                "request": message,
                "status": "thinking",
                "current_url": None,
                "steps": []
            }
            
            # Create Audit Log in database
            activity = UserActivity(
                task_id=task_id,
                user_id=email,
                request=message,
                status="thinking",
                steps="[]",
                information_used="[]",
                websites_visited="[]",
                actions_performed="[]",
                approval_requests="[]"
            )
            db.add(activity)
            db.commit()
        
        session = active_sessions[task_id]
        
        # Handle progressive profiling responses
        if session.get("pending_field"):
            pending_field = session.pop("pending_field")
            classification = "SENSITIVE_USER_DATA" if pending_field in ["name", "email", "phone", "address"] else "PRIVATE_USER_DATA"
            
            # Clean up standard conversation filler words (e.g. "i know python" -> "python")
            cleaned_val = message
            if pending_field == "skills":
                match = re.search(r'(?:i know|my skills are|skills are|skills:)\s*(.*)', message, re.IGNORECASE)
                if match:
                    cleaned_val = match.group(1).strip()
            elif pending_field == "name":
                match = re.search(r'(?:i am|my name is|name is|name:)\s*(.*)', message, re.IGNORECASE)
                if match:
                    cleaned_val = match.group(1).strip()
                    
            memory_service.add_memory_item(
                db=db,
                user_id=email,
                key=pending_field,
                value=cleaned_val,
                classification=classification,
                source="explicit"
            )
        
        # Log conversational step
        session["steps"].append({
            "action": "user_message",
            "description": f"User: {message}"
        })
        
        # 2. Check for Approval Responses
        if message == "proceed_execution":
            return self._execute_approved_plan(db, task_id)
        elif message == "cancel_execution":
            return self._cancel_plan(db, task_id)

        # 3. Retrieve Scoped Memories
        memories = memory_service.get_relevant_memories(db, email, session["request"])
        profile_data = {m.key: m.value for m in memories}
        used_keys = [m.key for m in memories]

        # Log memory usage for transparency
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
        if activity:
            activity.information_used = json.dumps(used_keys)
            db.commit()
            
        for m in memories:
            memory_service.log_memory_usage(
                db=db,
                memory_id=m.id,
                task_id=task_id,
                task_description=session["request"],
                website=session["current_url"]
            )

        # 4. Classify Intent & Check for Missing Information
        # If Gemini is configured, use it. Otherwise, use deterministic fallbacks for hackathon demo.
        if gemini_service.is_configured():
            try:
                intent: TaskIntent = gemini_service.classify_intent(session["request"])
                missing: MissingInformation = gemini_service.identify_missing_info(session["request"], profile_data)
                
                # If crucial info is missing, ask clarification questions
                if missing.missing_fields:
                    session["status"] = "asking"
                    session["pending_field"] = missing.missing_fields[0]
                    if activity:
                        activity.status = "asking"
                        db.commit()
                    return {
                        "task_id": task_id,
                        "status": "asking",
                        "response": missing.questions[0] if missing.questions else f"Could you please tell me your {missing.missing_fields[0]}?",
                        "clarification_needed": True,
                        "action_plan_required": False,
                        "browser_active": False
                    }
            except Exception as e:
                # Fallback on Gemini errors
                print(f"Warning: Gemini intent check failed: {e}")
                
        # Simple local progressive profiling logic:
        # If the task description includes "internship" and we don't have skills or name, ask for them.
        if "internship" in session["request"].lower():
            if not profile_data.get("skills"):
                session["status"] = "asking"
                session["pending_field"] = "skills"
                if activity:
                    activity.status = "asking"
                    db.commit()
                return {
                    "task_id": task_id,
                    "status": "asking",
                    "response": "I see you want to find software internships. What programming skills or tech stack should I filter for?",
                    "clarification_needed": True,
                    "action_plan_required": False,
                    "browser_active": False
                }
            if not profile_data.get("name"):
                session["status"] = "asking"
                session["pending_field"] = "name"
                if activity:
                    activity.status = "asking"
                    db.commit()
                return {
                    "task_id": task_id,
                    "status": "asking",
                    "response": "To help prepare applications, what is your full name?",
                    "clarification_needed": True,
                    "action_plan_required": False,
                    "browser_active": False
                }

        # 5. Launch Browser Session if needed
        # We need a browser if we are researching or doing web automation
        need_browser = any(w in session["request"].lower() for w in ["find", "search", "table", "internship", "buy", "register", "apply", "hotel", "trip"])
        
        if need_browser and not session["session_id"]:
            session["session_id"] = webcmd_client.create_session()
            session["status"] = "browsing"
            if activity:
                activity.status = "browsing"
                db.commit()

        # 6. Execute safe research/comparison (Milestone 3 & 6)
        if session["session_id"]:
            return self._run_browser_orchestration(db, task_id, message, profile_data)

        # Chat response fallback
        return {
            "task_id": task_id,
            "status": "completed",
            "response": f"I analyzed your request. Please let me know how I can help with browsing or mapping files.",
            "clarification_needed": False,
            "action_plan_required": False,
            "browser_active": False
        }

    def _run_browser_orchestration(
        self,
        db: Session,
        task_id: str,
        user_message: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes browser commands, captures screenshots, parses page state,
        and constructs action previews before consequential submissions.
        """
        session = active_sessions[task_id]
        session_id = session["session_id"]
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()

        # Update logs
        session["steps"].append({
            "action": "browsing_exploration",
            "tool": "webcmd_browser",
            "description": "Opening page viewport to search for relevant opportunities."
        })

        # Milestone 6 demo orchestration:
        query = session["request"].lower()
        
        # Define mock/local pages for fast, reliable hackathon automation
        # In a real environment, it navigates to actual target domains.
        # We construct a local dashboard form that simulates job portals or shopping carts.
        
        if "internship" in query:
            search_query = f"software engineering internships in {profile_data.get('address', 'Kolkata')} for skills {profile_data.get('skills', 'Python')}"
            session["current_url"] = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            webcmd_client.run_script(session_id, f'await page.goto("{session["current_url"]}");')
            screenshot = webcmd_client.get_screenshot(session_id)
            
            # Since this is consequential application, we must construct an Action Plan!
            plan = ActionPlan(
                task_id=task_id,
                user_id=session["email"],
                goal="Submit Application for Software Engineer Intern",
                website="example-internships.com",
                actions=json.dumps([
                    {"action_type": "navigate", "description": "Go to application page", "selector": None},
                    {"action_type": "fill", "description": "Fill name field", "selector": "#name", "value": profile_data.get("name", "Adrish")},
                    {"action_type": "fill", "description": "Fill skills field", "selector": "#skills", "value": profile_data.get("skills", "Python")},
                    {"action_type": "submit", "description": "Click Submit application button", "selector": "#submit-btn"}
                ]),
                information_to_be_sent=json.dumps({
                    "name": profile_data.get("name", "Adrish"),
                    "skills": profile_data.get("skills", "Python, ML")
                }),
                risk_level="CONSEQUENTIAL",
                approval_required=True,
                approval_status="pending",
                final_action="click submit button"
            )
            db.add(plan)
            db.commit()

            session["status"] = "waiting_approval"
            if activity:
                activity.status = "waiting_approval"
                activity.steps = json.dumps(session["steps"])
                activity.websites_visited = json.dumps(["example-internships.com"])
                db.commit()

            return {
                "task_id": task_id,
                "status": "waiting_approval",
                "response": "I found a match for a 'Software Engineering Intern' paying ₹15,000/month. I have mapped your profile fields and prepared the submission form. Please review the Action Preview below and click Approve to execute.",
                "clarification_needed": False,
                "action_plan_required": True,
                "action_plan": {
                    "goal": plan.goal,
                    "website": plan.website,
                    "actions": json.loads(plan.actions),
                    "information_to_be_sent": json.loads(plan.information_to_be_sent),
                    "risk_level": plan.risk_level
                },
                "browser_active": True,
                "browser_url": session["current_url"],
                "screenshot": screenshot
            }

        elif "table" in query or "laptop" in query:
            search_query = f"buy study table with drawers under 4000 rupees in {profile_data.get('address', 'Kolkata')}" if "table" in query else f"buy programming laptop under 60000 rupees"
            session["current_url"] = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            webcmd_client.run_script(session_id, f'await page.goto("{session["current_url"]}");')
            screenshot = webcmd_client.get_screenshot(session_id)
            
            # Checkout action plan
            plan = ActionPlan(
                task_id=task_id,
                user_id=session["email"],
                goal="Prepare Purchase for Study Table with Drawers (₹3,800)",
                website="example-shopping.com",
                actions=json.dumps([
                    {"action_type": "navigate", "description": "Navigate to product cart", "selector": None},
                    {"action_type": "fill", "description": "Fill shipping address", "selector": "#shipping-addr", "value": profile_data.get("address", "Kolkata")},
                    {"action_type": "click", "description": "Proceed to payment", "selector": "#payment-btn"}
                ]),
                information_to_be_sent=json.dumps({
                    "shipping_address": profile_data.get("address", "Kolkata, WB")
                }),
                risk_level="HIGH_RISK",  # Payment required boundary!
                approval_required=True,
                approval_status="pending",
                final_action="proceed to payment screen"
            )
            db.add(plan)
            db.commit()

            session["status"] = "waiting_approval"
            if activity:
                activity.status = "waiting_approval"
                activity.steps = json.dumps(session["steps"])
                activity.websites_visited = json.dumps(["example-shopping.com"])
                db.commit()

            return {
                "task_id": task_id,
                "status": "waiting_approval",
                "response": "I compared prices and found a sleek compact study table for ₹3,800 with drawers. I added it to your cart. Please review the checkout preview. Note that since online payment is required, MOSAIC will pause at checkout for manual payment completion.",
                "clarification_needed": False,
                "action_plan_required": True,
                "action_plan": {
                    "goal": plan.goal,
                    "website": plan.website,
                    "actions": json.loads(plan.actions),
                    "information_to_be_sent": json.loads(plan.information_to_be_sent),
                    "risk_level": plan.risk_level
                },
                "browser_active": True,
                "browser_url": session["current_url"],
                "screenshot": screenshot
            }

        else:
            # Default fallback search research
            session["current_url"] = "https://google.com"
            webcmd_client.run_script(session_id, 'await page.goto("https://google.com");')
            screenshot = webcmd_client.get_screenshot(session_id)
            
            session["status"] = "completed"
            if activity:
                activity.status = "completed"
                activity.result = "Found general details for task."
                activity.steps = json.dumps(session["steps"])
                db.commit()

            # Clean close
            webcmd_client.close_session(session_id)
            session["session_id"] = None
            
            return {
                "task_id": task_id,
                "status": "completed",
                "response": f"I have run a general search for your query. The results are visible in the viewport.",
                "clarification_needed": False,
                "action_plan_required": False,
                "browser_active": True,
                "browser_url": "https://google.com",
                "screenshot": screenshot
            }

    def _execute_approved_plan(self, db: Session, task_id: str) -> Dict[str, Any]:
        """
        Executes the final consequential step after human approval,
        logging audit logs and closing the browser.
        """
        session = active_sessions[task_id]
        session_id = session["session_id"]
        
        plan = db.query(ActionPlan).filter(
            ActionPlan.task_id == task_id,
            ActionPlan.approval_status == "approved"
        ).first()

        if not plan:
            return {
                "task_id": task_id,
                "status": "idle",
                "response": "No approved action plan found.",
                "clarification_needed": False,
                "action_plan_required": False,
                "browser_active": False
            }

        # Policy Engine validation check
        validation = tool_router.validate_action(
            "submit_application" if plan.risk_level == "CONSEQUENTIAL" else "execute_payment",
            {}
        )

        if not validation["allowed"] and validation.get("manual_action_required"):
            # Payments safety boundary enforced!
            session["steps"].append({
                "action": "manual_payment_block",
                "description": "Stopped automation due to payment boundary constraint. Displayed manual checkout warning."
            })
            
            activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
            if activity:
                activity.steps = json.dumps(session["steps"])
                activity.status = "completed"
                activity.result = "Checkout cart prepared. Manual payment required."
                db.commit()
                
            webcmd_client.close_session(session_id)
            session["session_id"] = None
            active_sessions.pop(task_id, None)

            return {
                "task_id": task_id,
                "status": "completed",
                "response": "⚠️ Manual Payment Required! MOSAIC safety policy blocks automated payments. The checkout details are loaded. Please proceed manually in the browser viewport to complete the transaction.",
                "clarification_needed": False,
                "action_plan_required": False,
                "browser_active": False
            }

        # Simulate submit click in browser
        webcmd_client.run_script(session_id, 'await page.goto("https://example.com");')
        screenshot = webcmd_client.get_screenshot(session_id)

        session["steps"].append({
            "action": "consequential_submission",
            "tool": "webcmd_browser",
            "description": f"Executed click on submit button for website {plan.website}."
        })

        # Save activity audit trail
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
        if activity:
            activity.steps = json.dumps(session["steps"])
            activity.status = "completed"
            activity.result = f"Successfully submitted forms to {plan.website}."
            db.commit()

        # Cleanup
        webcmd_client.close_session(session_id)
        session["session_id"] = None
        active_sessions.pop(task_id, None)

        return {
            "task_id": task_id,
            "status": "completed",
            "response": f"✓ Success! I have successfully completed the action plan and submitted your details to {plan.website}.",
            "clarification_needed": False,
            "action_plan_required": False,
            "browser_active": False
        }

    def _cancel_plan(self, db: Session, task_id: str) -> Dict[str, Any]:
        session = active_sessions[task_id]
        session_id = session["session_id"]

        plan = db.query(ActionPlan).filter(
            ActionPlan.task_id == task_id,
            ActionPlan.approval_status == "rejected"
        ).first()

        session["steps"].append({
            "action": "user_rejection",
            "description": "User rejected the prepared action preview."
        })

        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
        if activity:
            activity.steps = json.dumps(session["steps"])
            activity.status = "cancelled"
            activity.result = "Cancelled by user."
            db.commit()

        # Cleanup
        webcmd_client.close_session(session_id)
        session["session_id"] = None
        active_sessions.pop(task_id, None)

        return {
            "task_id": task_id,
            "status": "cancelled",
            "response": "Action preview cancelled. The browser session has been safely closed.",
            "clarification_needed": False,
            "action_plan_required": False,
            "browser_active": False
        }

agent_orchestrator = AgentOrchestrator()

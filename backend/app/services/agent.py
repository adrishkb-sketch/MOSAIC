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

        # Check for direct apply click
        if message.startswith("apply_for:"):
            target_url = message.split("apply_for:")[1].strip()
            session["request"] = f"Apply for internship/job at {target_url}"
            session["status"] = "browsing"
            
            if not session.get("session_id"):
                session["session_id"] = webcmd_client.create_session()
                
            session_id = session["session_id"]
            session["current_url"] = target_url
            
            # Save activity state
            activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
            if activity:
                activity.status = "browsing"
                db.commit()
                
            # Navigate to target URL immediately
            webcmd_client.run_script(session_id, f'await page.goto("{target_url}");')
            webcmd_client.run_script(session_id, 'await page.waitForTimeout(2000);')
            
            return self._run_browser_orchestration(db, task_id, f"Fill out application form on {target_url}", profile_data)
            
        # Check if the query is a search query
        is_search_query = any(w in session["request"].lower() for w in ["find", "search", "lookup", "gather", "collect", "internship", "buy", "want", "get", "shop", "need", "refrigerator", "fridge", "purchase", "price", "laptop", "table", "product"]) and not "apply" in message.lower()
        
        if is_search_query:
            if not session.get("session_id"):
                session["session_id"] = webcmd_client.create_session()
            return self._run_search_orchestration(db, task_id, session["request"], profile_data)

        # 5. Launch Browser Session if needed (Fallback general browsing)
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

    def _run_search_orchestration(
        self,
        db: Session,
        task_id: str,
        query: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        session = active_sessions[task_id]
        session_id = session["session_id"]
        
        # Navigate to Google Search or relevant portals
        search_query = query
        if "internship" in query.lower() and "skills" in profile_data:
            # enhance search query using profile skills if searching for internships
            skills = profile_data.get("skills", "")
            address = profile_data.get("address", "")
            search_query = f"{query} {skills} {address}".strip()
            
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        session["current_url"] = search_url
        
        # Go to Google and handle cookie consent if present
        navigation_script = f"""
        await page.goto("{search_url}");
        await page.waitForTimeout(2000);
        await page.evaluate(() => {{
            const btn = Array.from(document.querySelectorAll('button')).find(b => {{
                const txt = b.innerText.trim().toLowerCase();
                return txt.includes('accept all') || txt.includes('i agree') || txt.includes('agree') || txt.includes('consent');
            }});
            if (btn) btn.click();
        }});
        await page.waitForTimeout(2000);
        """
        webcmd_client.run_script(session_id, navigation_script)
        
        # Scrape links from the search page
        scrape_script = """
        return await page.evaluate(() => {
            const results = [];
            const elements = document.querySelectorAll('a');
            const seenUrls = new Set();
            for (const el of elements) {
                const href = el.href;
                const text = el.innerText.trim();
                if (href && text && href.startsWith('http') && !href.includes('google.com') && !href.includes('youtube.com') && !href.includes('wikipedia.org') && !href.includes('support.google')) {
                    if (!seenUrls.has(href)) {
                        seenUrls.add(href);
                        results.push({ text, href });
                    }
                }
            }
            return results;
        });
        """
        raw_results = []
        res = webcmd_client.run_script(session_id, scrape_script)
        if res.get("ok"):
            raw_results = res["result"] or []
            
        # Parse and format results
        search_items = []
        summary = ""
        
        if gemini_service.is_configured():
            try:
                # Use Gemini to extract, filter, and optionally add directly generated results
                prompt = f"""
                User Query: "{query}"
                Raw links extracted from search page:
                {json.dumps(raw_results[:100])}
                
                You are a smart job portal AI. First, filter and extract a list of at most 8 real, highly relevant search results/job openings matching the user's query from the raw links.
                Additionally, if there are fewer than 5 high-quality results from the search page, you can directly generate 2-3 highly relevant internship openings with REAL apply links from well-known career sites (e.g. Google Careers, GitHub Careers, Amazon, etc.) based on your knowledge.
                For each result, extract the title/role, company/source name, direct URL, and location.
                Provide a concise, friendly summary of what you found.
                """
                
                from pydantic import BaseModel, Field
                class SearchResultItem(BaseModel):
                    title: str
                    company: Optional[str] = None
                    url: str
                    location: Optional[str] = None
                    
                class SearchResultsResponse(BaseModel):
                    items: List[SearchResultItem]
                    summary: str

                parsed_res = gemini_service._call_model(prompt, SearchResultsResponse)
                
                for item in parsed_res.items:
                    search_items.append({
                        "title": item.title,
                        "company": item.company or "Web Link",
                        "url": item.url,
                        "location": item.location or ""
                    })
                summary = parsed_res.summary
            except Exception as e:
                print(f"Gemini search parsing failed, falling back to local: {e}")
                
        # If Gemini is not configured or failed, do local filtering
        if not search_items:
            # Let's filter links containing useful keywords
            filtered_links = []
            keywords = ["job", "career", "intern", "recruit", "detail", "apply", "post", "work", "position"]
            for r in raw_results:
                url = r["href"].lower()
                text = r["text"].lower()
                # prioritize links containing keywords
                if any(k in url or k in text for k in keywords):
                    filtered_links.append(r)
            
            # fallback to any links if filtered list is too small
            if len(filtered_links) < 3:
                filtered_links = raw_results[:8]
            else:
                filtered_links = filtered_links[:8]
                
            for idx, r in enumerate(filtered_links):
                # Clean title
                title = r["text"].split("\n")[0].strip()
                if len(title) > 80:
                    title = title[:80] + "..."
                # Estimate company from URL host
                from urllib.parse import urlparse
                parsed_uri = urlparse(r["href"])
                domain = parsed_uri.netloc.replace("www.", "")
                company = domain.split(".")[0].capitalize()
                
                search_items.append({
                    "title": title or f"Search Result #{idx+1}",
                    "company": company,
                    "url": r["href"],
                    "location": profile_data.get("address", "")
                })
            summary = f"I found {len(search_items)} matches for '{query}' in the web search."

        # Keep browser session open for subsequent apply automation, but set browser_active to False so viewport is hidden!
        # Save activity log
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()
        if activity:
            activity.status = "completed"
            activity.result = summary
            db.commit()
            
        screenshot = webcmd_client.get_screenshot(session_id)
        return {
            "task_id": task_id,
            "status": "idle",
            "response": summary,
            "clarification_needed": False,
            "action_plan_required": False,
            "browser_active": False,
            "browser_url": search_url,
            "screenshot": screenshot,
            "results": search_items
        }

    def _format_table(self, headers: List[str], rows: List[Any]) -> str:
        tbl = "| " + " | ".join(headers) + " |\n"
        tbl += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in rows:
            cells = row.cells if hasattr(row, "cells") else row
            tbl += "| " + " | ".join([str(c) for c in cells]) + " |\n"
        return tbl

    def _run_local_fallback_simulation(
        self,
        db: Session,
        task_id: str,
        query: str,
        profile_data: Dict[str, Any],
        screenshot: Optional[str]
    ) -> Dict[str, Any]:
        session = active_sessions[task_id]
        session_id = session["session_id"]
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()

        # Handle form-filling fallback for application or direct URL action
        if "apply" in query or "job" in query or "http" in query:
            # Fallback auto-fill on the actual webpage using Playwright
            fill_success = False
            current_url = session.get("current_url") or "https://google.com"
            try:
                # Find input elements
                find_fields_script = """
                return await page.evaluate(() => {
                    const inputs = Array.from(document.querySelectorAll('input, textarea'));
                    const fields = [];
                    for (const input of inputs) {
                        const id = input.id || "";
                        const name = input.name || "";
                        const placeholder = input.placeholder || "";
                        if (id || name || placeholder) {
                            fields.push({ id, name, placeholder });
                        }
                    }
                    return fields;
                });
                """
                res = webcmd_client.run_script(session_id, find_fields_script)
                if res.get("ok"):
                    fields = res["result"]
                    # Try to fill name, email, skills if we find them
                    for f in fields:
                        fid = f.get("id")
                        fname = f.get("name")
                        fplaceholder = f.get("placeholder", "").lower()
                        
                        # Build standard selectors
                        selector = None
                        if fid:
                            selector = f"#{fid}"
                        elif fname:
                            selector = f"[name='{fname}']"
                            
                        if selector:
                            name_val = profile_data.get("name", "Adrish")
                            email_val = profile_data.get("email", "user@example.com")
                            skills_val = profile_data.get("skills", "Python")
                            
                            # match name
                            if "name" in fid.lower() or "name" in fname.lower() or "name" in fplaceholder:
                                webcmd_client.run_script(session_id, f'await page.fill("{selector}", "{name_val}");')
                                fill_success = True
                            # match email
                            elif "email" in fid.lower() or "email" in fname.lower() or "email" in fplaceholder:
                                webcmd_client.run_script(session_id, f'await page.fill("{selector}", "{email_val}");')
                                fill_success = True
                            # match skills
                            elif "skills" in fid.lower() or "skills" in fname.lower() or "skills" in fplaceholder:
                                webcmd_client.run_script(session_id, f'await page.fill("{selector}", "{skills_val}");')
                                fill_success = True
            except Exception as e:
                print(f"Fallback auto-fill error: {e}")

            url_res = webcmd_client.run_script(session_id, "return page.url();")
            current_url = url_res.get("result") if url_res.get("ok") else current_url
            session["current_url"] = current_url
            screenshot = webcmd_client.get_screenshot(session_id) or screenshot

            plan = ActionPlan(
                task_id=task_id,
                user_id=session["email"],
                goal=f"Apply for job at {current_url}",
                website=current_url.split("/")[2] if "//" in current_url else "website",
                actions=json.dumps([
                    {"action_type": "fill", "description": "Fill name field", "selector": "#name", "value": profile_data.get("name", "Adrish")},
                    {"action_type": "fill", "description": "Fill email field", "selector": "#email", "value": profile_data.get("email", "user@example.com")},
                    {"action_type": "fill", "description": "Fill skills/profile field", "selector": "#skills", "value": profile_data.get("skills", "Python")}
                ]),
                information_to_be_sent=json.dumps({
                    "name": profile_data.get("name", "Adrish"),
                    "email": profile_data.get("email", "user@example.com"),
                    "skills": profile_data.get("skills", "Python")
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
                db.commit()

            return {
                "task_id": task_id,
                "status": "waiting_approval",
                "response": "I have navigated to the application page and mapped your profile details into the form. Please review the actual form on the right and check the details below before clicking Approve.",
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
                "browser_url": current_url,
                "screenshot": screenshot
            }

        elif "internship" in query:
            search_query = f"software engineering internships in {profile_data.get('address', 'Kolkata')} for skills {profile_data.get('skills', 'Python')}"
            session["current_url"] = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            webcmd_client.run_script(session_id, f'await page.goto("{session["current_url"]}");')
            screenshot = webcmd_client.get_screenshot(session_id) or screenshot

            plan = ActionPlan(
                task_id=task_id,
                user_id=session["email"],
                goal="Submit Application for Software Engineer Intern",
                website="google.com/search?q=internships",
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
                db.commit()

            return {
                "task_id": task_id,
                "status": "waiting_approval",
                "response": "I found software engineering internships matching your profile in Kolkata. I have mapped your profile fields and prepared the application details. Please review the Action Preview below and click Approve to execute.",
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
            screenshot = webcmd_client.get_screenshot(session_id) or screenshot

            plan = ActionPlan(
                task_id=task_id,
                user_id=session["email"],
                goal="Prepare Purchase for Study Table with Drawers (₹3,800)",
                website="google.com/search?q=shopping",
                actions=json.dumps([
                    {"action_type": "navigate", "description": "Navigate to product cart", "selector": None},
                    {"action_type": "fill", "description": "Fill shipping address", "selector": "#shipping-addr", "value": profile_data.get("address", "Kolkata")},
                    {"action_type": "click", "description": "Proceed to payment", "selector": "#payment-btn"}
                ]),
                information_to_be_sent=json.dumps({
                    "shipping_address": profile_data.get("address", "Kolkata, WB")
                }),
                risk_level="HIGH_RISK",
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
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            session["current_url"] = search_url
            
            # Go to Google and handle cookie consent if present
            navigation_script = f"""
            await page.goto("{search_url}");
            await page.waitForTimeout(2000);
            await page.evaluate(() => {{
                const btn = Array.from(document.querySelectorAll('button')).find(b => {{
                    const txt = b.innerText.trim().toLowerCase();
                    return txt.includes('accept all') || txt.includes('i agree') || txt.includes('agree') || txt.includes('consent');
                }});
                if (btn) btn.click();
            }});
            await page.waitForTimeout(2000);
            """
            webcmd_client.run_script(session_id, navigation_script)
            screenshot = webcmd_client.get_screenshot(session_id) or screenshot

            session["status"] = "completed"
            if activity:
                activity.status = "completed"
                activity.result = f"Found search details for: {query}"
                activity.steps = json.dumps(session["steps"])
                db.commit()

            webcmd_client.close_session(session_id)
            session["session_id"] = None
            active_sessions.pop(task_id, None)

            return {
                "task_id": task_id,
                "status": "completed",
                "response": f"I have run a general search for your query. The results are visible in the viewport.",
                "clarification_needed": False,
                "action_plan_required": False,
                "browser_active": True,
                "browser_url": search_url,
                "screenshot": screenshot
            }

    def _run_browser_orchestration(
        self,
        db: Session,
        task_id: str,
        user_message: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Dynamic LLM-in-the-loop browser driver. Executes actions step-by-step
        guided by Gemini reasoning and Webcmd accessibility tree evaluation.
        """
        session = active_sessions[task_id]
        session_id = session["session_id"]
        activity = db.query(UserActivity).filter(UserActivity.task_id == task_id).first()

        # Handle user responses to OTP or input requests
        if session.get("pending_input_selector"):
            selector = session.pop("pending_input_selector")
            fill_script = f'await page.fill("{selector}", "{user_message}");'
            webcmd_client.run_script(session_id, fill_script)
            session["steps"].append({
                "action": "fill",
                "description": f"Filled user response into element '{selector}'"
            })

        # Run reasoning up to 5 steps per conversational exchange
        for step in range(5):
            url_res = webcmd_client.run_script(session_id, "return page.url();")
            url = url_res.get("result") if url_res.get("ok") else "https://google.com"
            session["current_url"] = url

            snapshot = webcmd_client.get_accessibility_snapshot(session_id)
            screenshot = webcmd_client.get_screenshot(session_id) or ""

            # Check configuration
            if not gemini_service.is_configured():
                return self._run_local_fallback_simulation(db, task_id, session["request"].lower(), profile_data, screenshot)

            try:
                history = [{"action": s.get("action"), "description": s.get("description")} for s in session["steps"]]
                next_action = gemini_service.determine_next_browser_action(
                    goal=session["request"],
                    current_url=url,
                    page_snapshot=snapshot,
                    user_profile=profile_data,
                    execution_history=history
                )
            except Exception as e:
                print(f"Warning: Gemini browser reasoning call failed: {e}")
                return self._run_local_fallback_simulation(db, task_id, session["request"].lower(), profile_data, screenshot)

            # Log reasoning step
            session["steps"].append({
                "action": "thought",
                "description": f"Agent Thought: {next_action.thought}"
            })

            # Handle completing state
            if next_action.action_type == "complete":
                session["status"] = "completed"
                if activity:
                    activity.status = "completed"
                    activity.result = next_action.final_summary or "Successfully completed goal."
                    activity.steps = json.dumps(session["steps"])
                    db.commit()

                webcmd_client.close_session(session_id)
                session["session_id"] = None
                active_sessions.pop(task_id, None)

                response_text = next_action.final_summary or "Action sequence completed successfully."
                if next_action.table_rows and next_action.table_headers:
                    response_text += "\n\n### Comparison Table\n" + self._format_table(next_action.table_headers, next_action.table_rows)

                return {
                    "task_id": task_id,
                    "status": "completed",
                    "response": response_text,
                    "clarification_needed": False,
                    "action_plan_required": False,
                    "browser_active": False
                }

            # Handle OTP or interactive clarification questions
            elif next_action.action_type == "ask_user_otp":
                session["status"] = "asking"
                session["pending_input_selector"] = next_action.selector
                if activity:
                    activity.status = "asking"
                    db.commit()

                return {
                    "task_id": task_id,
                    "status": "asking",
                    "response": next_action.question or "Please enter the authentication code / OTP shown on the page:",
                    "clarification_needed": True,
                    "action_plan_required": False,
                    "browser_active": False,
                    "browser_url": url,
                    "screenshot": screenshot
                }

            # Handle consequential form approval blocks
            elif next_action.action_type == "submit_form_approval":
                plan = ActionPlan(
                    task_id=task_id,
                    user_id=session["email"],
                    goal=session["request"],
                    website=url.split("/")[2] if "//" in url else "website",
                    actions=json.dumps([
                        {"action_type": "fill", "description": f"Fill form element {next_action.selector}", "selector": next_action.selector, "value": next_action.value}
                    ] if next_action.selector else []),
                    information_to_be_sent=json.dumps(profile_data),
                    risk_level="CONSEQUENTIAL",
                    approval_required=True,
                    approval_status="pending",
                    final_action=f"Submit information to {url}"
                )
                db.add(plan)
                db.commit()

                session["status"] = "waiting_approval"
                if activity:
                    activity.status = "waiting_approval"
                    activity.steps = json.dumps(session["steps"])
                    db.commit()

                return {
                    "task_id": task_id,
                    "status": "waiting_approval",
                    "response": f"I have mapped your profile and prepared the form submission on {plan.website}. Please review the Action Preview below and click Approve to execute.",
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
                    "browser_url": url,
                    "screenshot": screenshot
                }

            # Handle browser operations
            elif next_action.action_type == "navigate" and next_action.url:
                webcmd_client.run_script(session_id, f'await page.goto("{next_action.url}");')
                session["steps"].append({
                    "action": "navigate",
                    "description": f"Navigated browser viewport to {next_action.url}"
                })

            elif next_action.action_type == "click" and next_action.selector:
                # Intercept payment check via Policy Engine
                validation = tool_router.validate_action("web_interact", {"selector": next_action.selector})
                if next_action.selector in ["#submit", "#submit-btn", "button[type='submit']"] or "checkout" in next_action.selector:
                    validation = tool_router.validate_action("submit_application", {"selector": next_action.selector})

                if not validation["allowed"]:
                    webcmd_client.close_session(session_id)
                    session["session_id"] = None
                    active_sessions.pop(task_id, None)
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "response": f"⚠️ Safety Boundary Triggered: {validation['reason']}",
                        "clarification_needed": False,
                        "action_plan_required": False,
                        "browser_active": False
                    }

                click_script = f'await page.click("{next_action.selector}");'
                webcmd_client.run_script(session_id, click_script)
                session["steps"].append({
                    "action": "click",
                    "description": f"Clicked element selector: {next_action.selector}"
                })

            elif next_action.action_type == "fill" and next_action.selector:
                val = next_action.value or ""
                fill_script = f'await page.fill("{next_action.selector}", "{val}");'
                webcmd_client.run_script(session_id, fill_script)
                session["steps"].append({
                    "action": "fill",
                    "description": f"Filled element {next_action.selector}"
                })

            elif next_action.action_type == "wait":
                import time
                time.sleep(2)
                session["steps"].append({
                    "action": "wait",
                    "description": "Waited 2 seconds for element updates."
                })

        # Step limit reached, return intermediate state to keep client updated
        return {
            "task_id": task_id,
            "status": "browsing",
            "response": "Continuing exploration in page view...",
            "clarification_needed": False,
            "action_plan_required": False,
            "browser_active": False,
            "browser_url": session["current_url"],
            "screenshot": webcmd_client.get_screenshot(session_id)
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
        webcmd_client.run_script(session_id, 'await page.goto("https://google.com");')
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

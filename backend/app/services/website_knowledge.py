import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import SharedWebsite
from datetime import datetime

class WebsiteKnowledgeService:
    def sanitize_value(self, value: str) -> str:
        """
        Regex patterns to identify and sanitize private data from selectors/workflow values.
        """
        if not isinstance(value, str):
            return str(value)

        # 1. Sanitize Email Addresses
        value = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '<user_email>', value)

        # 2. Sanitize Phone Numbers (e.g. +1 555-0199 or standard Indian numbers)
        value = re.sub(r'\+?\d{1,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '<user_phone>', value)

        # 3. Sanitize generic name strings (simulated for simplicity)
        # In a real setting, we match against active user memory values.
        return value

    def sanitize_actions(self, actions: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sanitizes all actions by replacing any personal profile values with generic tokens.
        """
        sanitized_actions = []
        for action in actions:
            action_copy = dict(action)
            val = action_copy.get("value")
            
            if val:
                # Direct check: does the value match any private profile item?
                matched = False
                for profile_key, profile_val in user_profile.items():
                    if str(profile_val).lower() == str(val).lower():
                        action_copy["value"] = f"<{profile_key}>"
                        matched = True
                        break
                
                # Apply regex sanitization if not matched directly
                if not matched:
                    action_copy["value"] = self.sanitize_value(str(val))
                    
            sanitized_actions.append(action_copy)
        return sanitized_actions

    def learn_workflow(
        self,
        db: Session,
        domain: str,
        name: str,
        workflow_name: str,
        actions: List[Dict[str, Any]],
        commands: List[str]
    ) -> SharedWebsite:
        """
        Persists a sanitized workflow to the shared global repository.
        """
        # Load or create shared website record
        website = db.query(SharedWebsite).filter(SharedWebsite.domain == domain).first()
        
        # Format workflows
        import json
        workflows_dict = {}
        if website:
            try:
                workflows_dict = json.loads(website.workflows or "{}")
            except Exception:
                workflows_dict = {}
        
        workflows_dict[workflow_name] = f"Execute actions: {', '.join([a.get('description', '') for a in actions])}"
        
        # Format commands
        existing_cmds = []
        if website:
            try:
                existing_cmds = json.loads(website.commands or "[]")
            except Exception:
                existing_cmds = []
        
        # Merge commands uniquely
        for cmd in commands:
            if cmd not in existing_cmds:
                existing_cmds.append(cmd)

        if website:
            website.workflows = json.dumps(workflows_dict)
            website.commands = json.dumps(existing_cmds)
            website.uses_count += 1
            website.last_updated = datetime.utcnow()
            db.commit()
            db.refresh(website)
            return website
        else:
            new_site = SharedWebsite(
                domain=domain,
                name=name,
                workflows=json.dumps(workflows_dict),
                commands=json.dumps(existing_cmds),
                success_rate=1.0,
                uses_count=1,
                fallback_strategies=json.dumps([
                    "Navigate step-by-step if click selector fails",
                    "Verify input labels if forms layout drifts"
                ])
            )
            db.add(new_site)
            db.commit()
            db.refresh(new_site)
            return new_site

website_knowledge_service = WebsiteKnowledgeService()

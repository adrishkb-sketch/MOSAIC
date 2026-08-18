import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import UserMemory, User
from app.core.config import settings

class MemoryService:
    def add_memory_item(
        self,
        db: Session,
        user_id: str,
        key: str,
        value: Any,
        classification: str,
        source: str = "explicit"
    ) -> UserMemory:
        # Check if user exists, if not, create them
        user = db.query(User).filter(User.email == user_id).first()
        if not user:
            user = User(email=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Convert value to string if it is a dict or list
        val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        
        # Check if key already exists for this user
        existing = db.query(UserMemory).filter(
            UserMemory.user_id == user_id,
            UserMemory.key == key
        ).first()

        if existing:
            existing.value = val_str
            existing.classification = classification
            existing.source = source
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_item = UserMemory(
                user_id=user_id,
                key=key,
                value=val_str,
                classification=classification,
                source=source,
                usage_history="[]"
            )
            db.add(new_item)
            db.commit()
            db.refresh(new_item)
            return new_item

    def get_memory_items(self, db: Session, user_id: str) -> List[UserMemory]:
        return db.query(UserMemory).filter(UserMemory.user_id == user_id).all()

    def get_memory_by_id(self, db: Session, memory_id: int) -> Optional[UserMemory]:
        return db.query(UserMemory).filter(UserMemory.id == memory_id).first()

    def update_memory_item(
        self,
        db: Session,
        memory_id: int,
        value: Any = None,
        classification: str = None,
        source: str = None
    ) -> Optional[UserMemory]:
        item = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
        if not item:
            return None
        
        if value is not None:
            val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            item.value = val_str
        if classification is not None:
            item.classification = classification
        if source is not None:
            item.source = source
            
        db.commit()
        db.refresh(item)
        return item

    def delete_memory_item(self, db: Session, memory_id: int) -> bool:
        item = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
        if not item:
            return False
        db.delete(item)
        db.commit()
        return True

    def clear_user_memories(self, db: Session, user_id: str) -> bool:
        db.query(UserMemory).filter(UserMemory.user_id == user_id).delete()
        db.commit()
        return True

    def log_memory_usage(
        self,
        db: Session,
        memory_id: int,
        task_id: str,
        task_description: str,
        website: Optional[str] = None
    ) -> None:
        item = db.query(UserMemory).filter(UserMemory.id == memory_id).first()
        if not item:
            return

        try:
            history = json.loads(item.usage_history or "[]")
        except Exception:
            history = []

        history.append({
            "task_id": task_id,
            "task_description": task_description,
            "website": website or "local_processing",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        item.usage_history = json.dumps(history)
        db.commit()

    def get_relevant_memories(
        self,
        db: Session,
        user_id: str,
        task_description: str
    ) -> List[UserMemory]:
        """
        Retrieves only memories relevant to the user request.
        Protects user privacy and optimizes prompt token count.
        """
        all_memories = self.get_memory_items(db, user_id)
        if not all_memories:
            return []

        # Convert task description to lowercase for simple keywords matching fallback
        desc_lower = task_description.lower()

        # Simple semantic categorization based on keywords
        category_map = {
            "education": ["internship", "job", "college", "degree", "university", "resume", "cv", "apply", "gpa", "academic", "hackathon"],
            "career": ["internship", "job", "career", "salary", "stipend", "resume", "cv", "apply", "skills", "experience", "github", "linkedin", "hackathon"],
            "shopping": ["buy", "shopping", "price", "table", "chair", "laptop", "furniture", "product", "cheapest", "compare"],
            "travel": ["trip", "hotel", "travel", "flight", "booking", "days", "vacation"],
            "basic": ["name", "email", "phone", "address", "gender"]
        }

        # Determine which categories are relevant
        relevant_categories = set()
        # Basic information is relevant if we are applying, registering or looking for jobs/internships/events
        if any(w in desc_lower for w in ["apply", "register", "book", "reserve", "checkout", "email", "submit", "internship", "job", "hackathon"]):
            relevant_categories.add("basic")

        for cat, keywords in category_map.items():
            if any(k in desc_lower for k in keywords):
                relevant_categories.add(cat)

        # If no specific categories detected, default to basic information
        if not relevant_categories:
            relevant_categories.add("basic")

        # Map memory keys to categories
        key_category_mapping = {
            "name": "basic",
            "email": "basic",
            "phone": "basic",
            "address": "basic",
            "education": "education",
            "degree": "education",
            "college": "education",
            "cgpa": "education",
            "experience": "career",
            "skills": "career",
            "projects": "career",
            "github": "career",
            "linkedin": "career",
            "resume": "career",
            "shoppingPreferences": "shopping",
            "shoppingBudget": "shopping",
            "travelPreferences": "travel",
            "travelBudget": "travel"
        }

        relevant_memories = []
        for memory in all_memories:
            mem_key = memory.key
            # Check mapping, default to including it if not specified (safest)
            mapped_cat = key_category_mapping.get(mem_key)
            if mapped_cat is None or mapped_cat in relevant_categories:
                relevant_memories.append(memory)

        return relevant_memories

memory_service = MemoryService()

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class UserMemory(Base):
    __tablename__ = "user_memories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Map to user email
    key = Column(String, index=True, nullable=False)      # e.g., 'name', 'skills'
    value = Column(Text, nullable=False)                  # JSON string or plain text
    classification = Column(String, nullable=False)       # PRIVATE_USER_DATA, SENSITIVE_USER_DATA, etc.
    source = Column(String, nullable=False)               # 'explicit', 'inferred'
    usage_history = Column(Text, default="[]")            # JSON list of task descriptions/dates
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserDocument(Base):
    __tablename__ = "user_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(Text, default="{}")
    created_at = Column(DateTime, server_default=func.now())

class UserActivity(Base):
    __tablename__ = "user_activities"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    request = Column(Text, nullable=False)
    interpreted_intent = Column(Text, nullable=True)
    steps = Column(Text, default="[]")                    # JSON list of agent execution steps
    information_used = Column(Text, default="[]")         # JSON list of memory items retrieved
    websites_visited = Column(Text, default="[]")         # JSON list of sites
    actions_performed = Column(Text, default="[]")        # JSON list of browser actions
    approval_requests = Column(Text, default="[]")        # JSON list
    final_action = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    status = Column(String, default="thinking")           # thinking, asking, browsing, waiting_approval, completed, failed, cancelled
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class ActionPlan(Base):
    __tablename__ = "action_plans"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    goal = Column(String, nullable=False)
    website = Column(String, nullable=False)
    actions = Column(Text, nullable=False)                 # JSON list of structured actions
    information_to_be_sent = Column(Text, default="{}")    # JSON map of data to be shared
    risk_level = Column(String, nullable=False)           # READ_ONLY, LOW_RISK, CONSEQUENTIAL, HIGH_RISK
    approval_required = Column(Boolean, default=True)
    approval_status = Column(String, default="pending")   # pending, approved, rejected
    final_action = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class SharedWebsite(Base):
    __tablename__ = "shared_websites"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    workflows = Column(Text, default="{}")                # JSON map of learned workflows (e.g. search, select)
    commands = Column(Text, default="[]")                 # JSON list of valid Webcmd command structures
    success_rate = Column(Float, default=1.0)
    last_validated = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    uses_count = Column(Integer, default=0)
    fallback_strategies = Column(Text, default="[]")       # JSON list of strings

import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.db.session import Base
from app.services.memory import memory_service
from app.db.models import UserMemory

# Create an in-memory SQLite database for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_add_and_get_memory_items(db):
    user_id = "test@example.com"
    
    # Add memory item
    item = memory_service.add_memory_item(
        db=db,
        user_id=user_id,
        key="name",
        value="Adrish",
        classification="PRIVATE_USER_DATA",
        source="explicit"
    )
    
    assert item.id is not None
    assert item.user_id == user_id
    assert item.key == "name"
    assert item.value == "Adrish"
    assert item.classification == "PRIVATE_USER_DATA"
    
    # Retrieve memories
    items = memory_service.get_memory_items(db, user_id)
    assert len(items) == 1
    assert items[0].key == "name"

def test_update_and_delete_memory(db):
    user_id = "test@example.com"
    item = memory_service.add_memory_item(
        db=db,
        user_id=user_id,
        key="skills",
        value=["Python", "C++"],
        classification="PRIVATE_USER_DATA",
        source="explicit"
    )
    
    # Update memory
    updated = memory_service.update_memory_item(
        db=db,
        memory_id=item.id,
        value=["Python", "C++", "React"]
    )
    assert updated.value == '["Python", "C++", "React"]'
    
    # Delete memory
    deleted = memory_service.delete_memory_item(db, item.id)
    assert deleted is True
    
    items = memory_service.get_memory_items(db, user_id)
    assert len(items) == 0

def test_scoped_memory_retrieval(db):
    user_id = "test@example.com"
    
    # Add career and shopping memories
    memory_service.add_memory_item(db, user_id, "skills", "Python, ML", "PRIVATE_USER_DATA")
    memory_service.add_memory_item(db, user_id, "shoppingBudget", "5000", "EXPLICIT_PREFERENCE")
    memory_service.add_memory_item(db, user_id, "name", "Adrish", "PRIVATE_USER_DATA")
    
    # Search for internship task - should retrieve skills and name, not shopping budget
    internship_memories = memory_service.get_relevant_memories(
        db=db,
        user_id=user_id,
        task_description="Apply to python internships"
    )
    keys = [m.key for m in internship_memories]
    assert "skills" in keys
    assert "name" in keys
    assert "shoppingBudget" not in keys
    
    # Search for shopping task - should retrieve shopping budget, not skills
    shopping_memories = memory_service.get_relevant_memories(
        db=db,
        user_id=user_id,
        task_description="Find study table under 4000"
    )
    keys = [m.key for m in shopping_memories]
    assert "shoppingBudget" in keys
    assert "skills" not in keys

def test_log_memory_usage(db):
    user_id = "test@example.com"
    item = memory_service.add_memory_item(db, user_id, "name", "Adrish", "PRIVATE_USER_DATA")
    
    memory_service.log_memory_usage(
        db=db,
        memory_id=item.id,
        task_id="task-123",
        task_description="Apply for internship",
        website="example.com"
    )
    
    db.refresh(item)
    import json
    history = json.loads(item.usage_history)
    assert len(history) == 1
    assert history[0]["task_id"] == "task-123"
    assert history[0]["website"] == "example.com"

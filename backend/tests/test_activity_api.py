import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.models import UserActivity

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_activity_api():
    email = "audit_test@example.com"
    task_id = "test-task-999"
    
    # Manually inject an activity record into test database
    db = SessionLocal()
    activity = UserActivity(
        task_id=task_id,
        user_id=email,
        request="Find software engineering internships paying at least 5000",
        interpreted_intent="research",
        steps='[{"step": "search", "tool": "web_research", "output": "Found 3 internships"}]',
        information_used='["skills", "location"]',
        websites_visited='["example.com"]',
        actions_performed='["search_input", "click"]',
        approval_requests='[]',
        result="Internship A, Internship B",
        status="completed"
    )
    db.add(activity)
    db.commit()
    db.close()
    
    # 1. Test listing activities
    response = client.get(f"/api/activity/logs?email={email}")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["task_id"] == task_id
    assert logs[0]["request"] == "Find software engineering internships paying at least 5000"
    
    # 2. Test detailed task view
    response = client.get(f"/api/activity/logs/{task_id}")
    assert response.status_code == 200
    details = response.json()
    assert details["task_id"] == task_id
    assert details["status"] == "completed"
    assert "example.com" in details["websites_visited"]

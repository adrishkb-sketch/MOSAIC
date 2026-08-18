import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.models import UserMemory

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_agent_chat_and_approval_workflow():
    email = "agent_test@example.com"
    
    # 1. First chat query (internships) - should ask for skills due to progressive profiling
    response = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "Find me software engineering internships."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["clarification_needed"] is True
    assert "skills" in data["response"].lower()
    task_id = data["task_id"]

    # 2. Save skills to My Memory (simulate user profile setup)
    db = SessionLocal()
    mem = UserMemory(
        user_id=email,
        key="skills",
        value="Python, React",
        classification="PRIVATE_USER_DATA",
        source="explicit",
        usage_history="[]"
    )
    mem2 = UserMemory(
        user_id=email,
        key="name",
        value="Adrish",
        classification="SENSITIVE_USER_DATA",
        source="explicit",
        usage_history="[]"
    )
    db.add(mem)
    db.add(mem2)
    db.commit()
    db.close()

    # 3. Chat again with the skills resolved - should trigger browser search and return action plan
    response = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "Find me software engineering internships.", "task_id": task_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "waiting_approval"
    assert data["action_plan_required"] is True
    assert data["action_plan"] is not None
    assert data["browser_active"] is True
    assert data["screenshot"] is not None
    assert data["screenshot"].startswith("data:image/png;base64,")

    # 4. Submit approval to update plan status
    response = client.post(
        f"/api/agent/action-plan/{task_id}/approve",
        json={"approved": True}
    )
    assert response.status_code == 200
    approval_res = response.json()
    assert approval_res["status"] == "success"

    # 5. Call chat endpoint with proceed_execution to run the approved plan
    response = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "proceed_execution", "task_id": task_id}
    )
    assert response.status_code == 200
    chat_res = response.json()
    assert chat_res["status"] == "completed"
    assert "submitted" in chat_res["response"].lower() or "success" in chat_res["response"].lower()

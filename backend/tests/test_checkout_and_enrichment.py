import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.db.models import UserMemory
from app.services.gemini import gemini_service, BrowserNextAction
from app.services.webcmd import webcmd_client
from app.services.agent import agent_orchestrator, active_sessions

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    for table in reversed(Base.metadata.sorted_tables):
        with engine.connect() as conn:
            conn.execute(table.delete())
            conn.commit()

def test_proactive_profile_enrichment_flow():
    email = "enrich_user@example.com"
    db = SessionLocal()
    db.add(UserMemory(
        user_id=email,
        key="skills",
        value="Python, React",
        classification="PRIVATE_USER_DATA",
        source="explicit",
        usage_history="[]"
    ))
    db.add(UserMemory(
        user_id=email,
        key="name",
        value="Alex",
        classification="SENSITIVE_USER_DATA",
        source="explicit",
        usage_history="[]"
    ))
    db.commit()
    db.close()

    # Step 1: User asks to find internships. The agent should proactively ask if user wants to add more skills.
    response = client.post(
        "/api/agent/chat",
        json={"email": email, "message": "Find me software engineering internships."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["clarification_needed"] is True
    assert "Python, React" in data["response"]
    assert "add" in data["response"].lower() or "skills" in data["response"].lower()
    task_id = data["task_id"]

    # Step 2: User responds by adding more skills (e.g. "Add Docker and AWS")
    with patch.object(webcmd_client, "navigate_to", return_value={"ok": True}), \
         patch.object(webcmd_client, "run_script", return_value={"ok": True, "result": [
             {"text": "Python Backend Intern ₹30,000", "href": "https://internshala.com/python-intern"}
         ]}), \
         patch.object(webcmd_client, "get_screenshot", return_value="data:image/png;base64,mock"):

        response2 = client.post(
            "/api/agent/chat",
            json={"email": email, "message": "Also add Docker, TypeScript, and AWS", "task_id": task_id}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["results"] is not None

        # Verify that UserMemory was updated with enriched skills
        db = SessionLocal()
        mem = db.query(UserMemory).filter(UserMemory.user_id == email, UserMemory.key == "skills").first()
        assert mem is not None
        assert "Docker" in mem.value
        assert "TypeScript" in mem.value
        db.close()

def test_live_site_address_and_payment_boundary_traversal():
    email = "checkout_user@example.com"
    task_id = "test_checkout_task_456"

    db = SessionLocal()
    db.add(UserMemory(user_id=email, key="name", value="Jane Doe", classification="SENSITIVE_USER_DATA", source="explicit", usage_history="[]"))
    db.add(UserMemory(user_id=email, key="address", value="123 Tech Park, Salt Lake", classification="SENSITIVE_USER_DATA", source="explicit", usage_history="[]"))
    db.add(UserMemory(user_id=email, key="pincode", value="700091", classification="SENSITIVE_USER_DATA", source="explicit", usage_history="[]"))
    db.commit()
    db.close()

    active_sessions[task_id] = {
        "session_id": "sess_checkout",
        "email": email,
        "request": "Buy this laptop on Flipkart",
        "status": "browsing",
        "state": "idle",
        "current_url": "https://www.flipkart.com/acer-nitro-v",
        "steps": [],
        "available_options": [],
        "browser_active": True
    }

    # Simulate shipping screen followed by payment boundary screen
    with patch.object(webcmd_client, "extract_page_details", return_value={
             "url": "https://www.flipkart.com/checkout/init",
             "title": "Payment Options",
             "is_payment_screen": True,
             "is_shipping_screen": False,
             "is_otp_screen": False,
             "is_login_screen": False,
             "items": [],
             "inputs": [],
             "buttons": []
         }), \
         patch.object(webcmd_client, "get_screenshot", return_value="data:image/png;base64,mock"):

        response = client.post(
            "/api/agent/chat",
            json={"email": email, "message": "buy now", "task_id": task_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "waiting_approval"
        assert data["action_plan_required"] is True
        assert "Payment Safety Boundary" in data["response"]
        assert data["action_plan"]["risk_level"] == "HIGH_RISK"

def test_chat_based_login_credentials_submission():
    email = "login_user@example.com"
    task_id = "test_login_task_789"

    active_sessions[task_id] = {
        "session_id": "sess_login",
        "email": email,
        "request": "Order item on portal",
        "status": "asking",
        "state": "awaiting_login_creds",
        "pending_login_selector": "#user-password",
        "current_url": "https://www.portal.com/login",
        "steps": [],
        "available_options": [],
        "browser_active": True
    }

    with patch.object(webcmd_client, "fill_element", return_value=True) as mock_fill, \
         patch.object(webcmd_client, "click_element", return_value=True) as mock_click, \
         patch.object(webcmd_client, "extract_page_details", return_value={
             "url": "https://www.portal.com/checkout/payment",
             "title": "Payment Selection",
             "is_payment_screen": True,
             "is_shipping_screen": False,
             "is_otp_screen": False,
             "is_login_screen": False,
             "items": [],
             "inputs": [],
             "buttons": []
         }), \
         patch.object(webcmd_client, "get_screenshot", return_value="data:image/png;base64,mock"):

        response = client.post(
            "/api/agent/chat",
            json={"email": email, "message": "SecretPass123!", "task_id": task_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert mock_fill.called
        assert mock_click.called
        # Verify it automatically proceeded after login to the payment safety boundary
        assert data["status"] == "waiting_approval"
        assert "Payment Safety Boundary" in data["response"]
